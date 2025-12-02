# Copyright (c) 2025 Mimer Information Technology

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# See license for more details.

import os
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from mimer_mcp_server.database import (
    DDLGenerator,
    SchemaInspector,
    StoredProcedureManager,
    init_db_pool,
    close_db_pool,
    get_connection,
)
import logging
import mimer_mcp_server.config as config
from typing import Annotated, Literal
import re

from contextlib import asynccontextmanager


def setup_logging(
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
) -> logging.Logger:
    """Set up logging for the MCP server based on configuration."""

    try:
        numeric_level = getattr(logging, log_level.upper())
    except AttributeError:
        raise ValueError(
            f"Invalid log level: {log_level}. "
            f"Must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL"
        )

    logger = logging.getLogger("mimer_mcp_server")
    logger.setLevel(numeric_level)

    # Create console handler
    console = logging.StreamHandler()
    console.setLevel(numeric_level)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console.setFormatter(formatter)
    logger.addHandler(console)
    logger.info(f"Logging level set to {numeric_level}")

    return logger


logger = setup_logging(config.LOG_LEVEL)


@asynccontextmanager
async def lifespan(server: FastMCP):
    """Manage database connection pool lifecycle for the FastMCP server.

    This context manager:
    - Initializes the database connection pool on server startup
    - Keeps it alive for the duration of the server's lifetime
    - Closes it on server shutdown
    """

    # Startup: Initialize the database connection pool
    logger.debug("Starting up: Initializing the database connection pool")
    try:
        init_db_pool()
        logger.info("Database connection pool established successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database connection pool: {e}")
        raise

    try:
        yield
    finally:
        # Shutdown: Close the database connection pool (if initialized)
        logger.info("Shutting down: Closing the database connection pool")
        try:
            close_db_pool()
            logger.info("Database connection pool closed successfully")
        except Exception as e:
            logger.error(f"Failed to close database connection pool: {e}")


# Create MCP server
mcp = FastMCP(name="Mimer MCP Server", lifespan=lifespan)


@mcp.tool(
    description="List all available schemas in the database",
)
def list_schemas() -> list[str]:
    """List all available schemas in the database.

    Returns:
        A list of schema names."""

    try:
        with get_connection() as con:
            logger.debug("Listing schemas")
            with con.cursor() as cursor:
                cursor.execute("SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA")
                return [row[0] for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Error listing schemas: {e}")
        raise ToolError(f"Error listing schemas: {e}")


@mcp.tool(
    description="List table names from the specified schema",
)
def list_table_names(
    schema: Annotated[str, "Schema name to filter tables"],
) -> list[str]:
    """List table names from the specified schema.

    Args:
        schema (str): The schema name to filter tables.

    Returns:
        A list of table names in the given schema.

    Raises:
        ValueError: if the schema does not exist or no tables are found."""
    try:
        with get_connection() as con:
            logger.debug(f"Listing table names for schema '{schema}'")
            cursor = con.cursor()
            query = (
                "SELECT TABLE_NAME "
                "FROM INFORMATION_SCHEMA.TABLES "
                "WHERE TABLE_TYPE = 'BASE TABLE' "
                "AND TABLE_SCHEMA <> 'SYSTEM' "
                "AND TABLE_SCHEMA = ?"
            )
            cursor.execute(query, [schema])
            tables = cursor.fetchall()

            if not tables:
                # Check if schema exists
                if not SchemaInspector(con).schema_exists(schema):
                    message = (
                        f"Schema '{schema}' does not exist or no tables found in it."
                    )
                    logger.error(message)
                    cursor.close()
                    raise ValueError(message)

            result = [table[0] for table in tables]
            cursor.close()
            return result
    except Exception as e:
        logger.error(f"Error listing table names for schema '{schema}': {e}")
        raise ToolError(f"Error listing table names for schema '{schema}': {e}")


@mcp.tool(description="Get detailed table schemas and sample rows")
def get_table_info(
    table_names: Annotated[list[str], "Names of the tables"],
    schema: Annotated[str, "Schema name"],
    sample_size: Annotated[int, "Number of sample rows to include"] = 3,
) -> str:
    """Get detailed table schemas and sample rows.

    Args:
        table_names (list[str]): List of table names to get info for.
        schema (str): The schema name to get info for.
        sample_size (int): Number of sample rows to include.

    Returns:
        Formatted string with CREATE TABLE and sample rows.
    """
    logger.debug(f"Getting table info for tables '{table_names}' in schema '{schema}'")
    try:
        with get_connection() as con:
            return DDLGenerator(con).format_table_info_with_samples(
                table_names,
                schema,
                sample_size,
            )
    except Exception as e:
        logger.error(
            f"Error getting table info for tables '{table_names}' in schema '{schema}': {e}"
        )
        raise ToolError(
            f"Error getting table info for tables '{table_names}' in schema '{schema}': {e}"
        )


@mcp.tool(
    description=(
        "Execute a SQL SELECT query and return the results as a list of dictionaries."
        "All queries must strictly follow SQL:2003 standard, e.g. FETCH, COALESCE, CASE."
        "Avoid vendor-specific syntax."
    )
)
def execute_query(
    query: Annotated[str, "SQL query to execute"],
    params: Annotated[list[str], "Parameters for the SQL query"] = [],
) -> list[dict]:
    """Execute a SQL query and return the results as a list of dictionaries.

    Args:
        query (str): The SQL query to execute.
        params (list[str]): Parameters for the SQL query.

    Returns:
        A list of rows, each represented as a dictionary mapping column names to values.

    Raises:
        ValueError: if the query is not a SELECT statement.
    """
    logger.debug(f"Executing query: {query}")
    if not re.match(r"^\s*SELECT", query, re.IGNORECASE):
        raise ValueError("Only SELECT queries are allowed.")
    else:
        try:
            with get_connection() as con:
                with con.cursor() as cursor:
                    cursor.execute(query, params)
                    columns = [desc[0] for desc in cursor.description]
                    rows = cursor.fetchall()
                    result = [dict(zip(columns, row)) for row in rows]
                    logger.debug(f"Read query returned {len(result)} rows")
                    return result
        except Exception as e:
            logger.error(f"Database error executing query '{query}': {e}")
            raise ToolError(f"Database error executing query '{query}': {e}")


@mcp.tool(
    description="List all stored procedures in the database",
)
def list_stored_procedures() -> list[dict]:
    """List all stored procedures in the database (only 'READS SQL DATA' procedures).

    Returns:
        A list of stored procedures with schema and name.
    """
    try:
        with get_connection() as con:
            return StoredProcedureManager(con).list_stored_procedures()
    except Exception as e:
        logger.error(f"Error listing stored procedures: {e}")
        raise ToolError(f"Error listing stored procedures: {e}")


@mcp.tool(
    description="Get the definition of a stored procedure",
)
def get_stored_procedure_definition(
    procedure_schema: Annotated[str, "Schema name of the stored procedure"],
    procedure_name: Annotated[str, "Name of the stored procedure"],
) -> str:
    """Get the definition of a stored procedure.

    Args:
        procedure_schema (str): Schema name of the stored procedure.
        procedure_name (str): Name of the stored procedure.

    Returns:
        The DDL definition of the stored procedure.
    """
    try:
        with get_connection() as con:
            return StoredProcedureManager(con).get_stored_procedure_definition(
                procedure_schema, procedure_name
            )
    except Exception as e:
        logger.error(
            f"Error getting stored procedure definition for {procedure_schema}.{procedure_name}: {e}"
        )
        raise ToolError(
            f"Error getting stored procedure definition for {procedure_schema}.{procedure_name}: {e}"
        )


@mcp.tool(
    description="Get the parameters of a stored procedure",
)
def get_stored_procedure_parameters(
    procedure_schema: Annotated[str, "Schema name of the stored procedure"],
    procedure_name: Annotated[str, "Name of the stored procedure"],
) -> dict:
    """Get the parameters of a stored procedure.

    Args:
        procedure_schema (str): Schema name of the stored procedure.
        procedure_name (str): Name of the stored procedure.

    Returns:
        A dictionary of parameter names and their types.
    """
    try:
        with get_connection() as con:
            return StoredProcedureManager(con).get_stored_procedure_parameters(
                procedure_schema, procedure_name
            )
    except Exception as e:
        logger.error(
            f"Error getting stored procedure parameters for {procedure_schema}.{procedure_name}: {e}"
        )
        raise ToolError(
            f"Error getting stored procedure parameters for {procedure_schema}.{procedure_name}: {e}"
        )


@mcp.tool(
    description="Execute a stored procedure in the database. Call this tool with the appropriate stored procedure name and parameters based on what procedures are available (use list_stored_procedures first if unsure).",
)
def execute_stored_procedure(
    procedure_schema: Annotated[str, "Schema name of the stored procedure"],
    procedure_name: Annotated[str, "Name of the stored procedure"],
    parameters: Annotated[
        str,
        "JSON string of parameters for the stored procedure mapping parameter names to values",
    ],
) -> dict:
    """Execute a stored procedure in the database. Call this tool with the appropriate stored procedure name and parameters based on what procedures are available (use list_stored_procedures first if unsure).

    Args:
        procedure_schema (str): Schema name of the stored procedure.
        procedure_name (str): Name of the stored procedure.
        parameters (str): JSON string of parameters for the stored procedure mapping parameter names to values.

    Returns:
        The result of the stored procedure execution as a dictionary.
    """
    try:
        with get_connection() as con:
            return StoredProcedureManager(con).execute_stored_procedure(
                procedure_schema, procedure_name, parameters
            )
    except Exception as e:
        logger.error(
            f"Error executing stored procedure {procedure_schema}.{procedure_name}: {e}"
        )
        raise ToolError(
            f"Error executing stored procedure {procedure_schema}.{procedure_name}: {e}"
        )


def main():
    """Entry point for the Mimer MCP server"""
    # setup_logging(level=config.LOG_LEVEL)

    # Start the server
    logger.info("Starting Mimer MCP server...")
    transport = os.getenv("MCP_TRANSPORT", "stdio")

    if transport == "stdio":
        mcp.run()
    elif transport == "http":
        host = os.getenv("MCP_HTTP_HOST", "0.0.0.0")
        port = int(os.getenv("MCP_HTTP_PORT", "3333"))
        logger.info(f"Starting MCP HTTP server on {host}:{port}")
        mcp.run(transport="http", host=host, port=port)
    else:
        raise ValueError(f"Unknown MCP_TRANSPORT: {transport}")


if __name__ == "__main__":
    main()
