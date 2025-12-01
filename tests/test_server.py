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

import pytest
from fastmcp import Client
from mcp.types import TextContent
from fastmcp.exceptions import ToolError
import logging
import os
from mimer_mcp_server.server import mcp, setup_logging, logger as server_logger
from mimer_mcp_server.database import connection
from mimer_mcp_server import config


@pytest.fixture
def mock_db_connection(monkeypatch):
    """Fixture to mock database connection."""
    monkeypatch.setattr(
        connection,
        "DB_CONFIG",
        {
            "dsn": "testdb",
            "user": "MIMER_STORE",
            "password": "GoodiesRUs",
        },  # Use example database credentials
    )


@pytest.fixture
def restore_logger_level():
    """Fixture to save and restore the server logger level after test."""
    original_level = server_logger.level
    yield
    server_logger.setLevel(original_level)


@pytest.mark.asyncio
async def test_list_tools():
    """Test listing available tools."""
    async with Client(mcp) as client:
        result = await client.list_tools()
    assert len(result) == 8


@pytest.mark.asyncio
async def test_ping():
    async with Client(mcp) as client:
        await client.ping()
        assert True  # If no exception, ping is successful


## --- Tests for Logging Setup ---


def test_setup_logging():
    """Test if logging is set to default value (INFO) if none is provided."""
    # Capture raw env value before config processing
    raw_env_value = os.getenv("MCP_LOG_LEVEL")

    config_log_level = config.LOG_LEVEL
    assert config_log_level == (raw_env_value or "INFO")

    # monkeypatch.setattr(config, "LOG_LEVEL", None)
    logger = setup_logging(config.LOG_LEVEL)

    # Print for debugging (visible with pytest -s)
    print(f"\nMCP_LOG_LEVEL from .env: {raw_env_value!r}")
    print(f"LOG_LEVEL from config.py: {config_log_level!r}")
    print(
        f"Logger level after setup: {logger.level} ({logging.getLevelName(logger.level)})"
    )

    assert logger.level == logging.INFO


def test_setup_logging_debug(monkeypatch, restore_logger_level):
    """Test if logging is set to DEBUG level when specified."""
    # Capture raw env value before config processing
    raw_env_value = os.getenv("MCP_LOG_LEVEL")

    monkeypatch.setattr(config, "LOG_LEVEL", "DEBUG")
    logger = setup_logging(config.LOG_LEVEL)

    # Print for debugging (visible with pytest -s)
    print(f"\nMCP_LOG_LEVEL from .env: {raw_env_value!r}")
    print(f"LOG_LEVEL from config.py: {config.LOG_LEVEL!r}")
    print(
        f"Logger level after setup: {logger.level} ({logging.getLevelName(logger.level)})"
    )

    assert logger.level == logging.DEBUG


def test_server_logger_level():
    """Test if server logger is set to default value (INFO) if no envvar is provided."""
    expected_level = logging.getLevelName(config.LOG_LEVEL)

    # Print for debugging (visible with pytest -s)
    print(f"\nconfig.LOG_LEVEL: {config.LOG_LEVEL!r}")
    print(f"Expected numeric level: {expected_level}")
    print(
        f"Actual logger level: {server_logger.level} ({logging.getLevelName(server_logger.level)})"
    )

    assert server_logger.level == expected_level, (
        f"Expected logger level {expected_level} ({config.LOG_LEVEL}), "
        f"got {server_logger.level} ({logging.getLevelName(server_logger.level)})"
    )


@pytest.mark.asyncio
async def test_server_logger_level_with_client():
    """Test if server logger maintains configured log level when server is running."""
    async with Client(mcp):
        expected_level = logging.getLevelName(config.LOG_LEVEL)

        # Print for debugging (visible with pytest -s)
        print(f"\nconfig.LOG_LEVEL: {config.LOG_LEVEL!r}")
        print(f"Expected numeric level: {expected_level}")
        print(
            f"Actual logger level: {server_logger.level} ({logging.getLevelName(server_logger.level)})"
        )

        assert server_logger.level == expected_level, (
            f"Expected logger level {expected_level} ({config.LOG_LEVEL}), "
            f"got {server_logger.level} ({logging.getLevelName(server_logger.level)})"
        )


@pytest.mark.asyncio
async def test_server_logger_debug_with_client(monkeypatch, restore_logger_level):
    """Test if server logger is set to DEBUG level when specified and server is running."""
    import importlib

    # Set env var before importing config
    monkeypatch.setattr(config, "LOG_LEVEL", "DEBUG")

    # Reload server to apply new config
    from mimer_mcp_server import server

    importlib.reload(server)

    async with Client(mcp):
        expected_level = logging.DEBUG

        # Print for debugging (visible with pytest -s)
        print(f"\nconfig.LOG_LEVEL: {config.LOG_LEVEL!r}")
        print(f"Expected numeric level: {expected_level}")
        print(
            f"Actual logger level: {server_logger.level} ({logging.getLevelName(server_logger.level)})"
        )

        assert server_logger.level == expected_level


def test_server_logger_invalid_type(monkeypatch):
    """Test setup_logging with invalid type raises ValueError."""
    import importlib

    # Set invalid log level before reloading
    monkeypatch.setattr(config, "LOG_LEVEL", "INVALID_LEVEL")

    from mimer_mcp_server import server

    with pytest.raises(ValueError, match="Invalid log level: INVALID_LEVEL"):
        importlib.reload(server)


# --- Tests for Database Schema Tools ---


@pytest.mark.asyncio
async def test_list_schemas_success(mock_db_connection):
    """Test successful listing of database schemas."""
    async with Client(mcp) as client:
        result = await client.call_tool("list_schemas")

    # FastMCP Client gives a structured result object:
    # - data: unwrapped values (int/str/bool or parsed object)
    # - structured_content: raw structured payload
    # - content: MCP content blocks (e.g., TextContent)
    assert isinstance(result.data, list)
    assert len(result.data) == 4  # Verify it has expected number of schemas
    assert result.structured_content == {
        "result": [
            "mimer_store",
            "mimer_store_book",
            "mimer_store_music",
            "mimer_store_web",
        ]
    }
    assert isinstance(result.content[0], TextContent)
    assert (
        result.content[0].text
        == '["mimer_store","mimer_store_book","mimer_store_music","mimer_store_web"]'
    )


@pytest.mark.asyncio
async def test_table_names_success(mock_db_connection):
    """Test listing table names from a valid schema."""
    async with Client(mcp) as client:
        result = await client.call_tool("list_table_names", {"schema": "mimer_store"})
    assert isinstance(result.data, list)
    assert len(result.data) == 12  # Verify it has expected number of tables


@pytest.mark.asyncio
async def test_table_names_invalid_schema():
    """Test listing table names from an invalid schema."""
    async with Client(mcp) as client:
        with pytest.raises(ToolError):
            await client.call_tool(
                "list_table_names", {"schema": "non_existent_schema"}
            )


@pytest.mark.asyncio
async def test_get_table_info(mock_db_connection):
    """Test successful retrieval of table info."""
    async with Client(mcp) as client:
        result = await client.call_tool(
            "get_table_info", {"schema": "mimer_store", "table_names": ["items"]}
        )
        assert isinstance(result.data, str)
        assert 'CREATE TABLE "items"' in result.data

        # Test with custom sample size
        custom_result = await client.call_tool(
            "get_table_info",
            {"schema": "mimer_store", "table_names": ["items"], "sample_size": 5},
        )
        assert "5 rows from items table:" in custom_result.data


# --- Tests for Query Execution Tool ---


@pytest.mark.asyncio
async def test_execute_query_success(mock_db_connection):
    """Test execution of query with valid syntax."""
    async with Client(mcp) as client:
        query = """SELECT product, product_id\nFROM mimer_store.products\nFETCH FIRST 10 ROWS ONLY"""
        result = await client.call_tool("execute_query", {"query": query})
    assert isinstance(result.data, list)
    assert len(result.data) == 10


@pytest.mark.asyncio
async def test_execute_query_non_select(mock_db_connection):
    """Test execution of non-SELECT query."""
    async with Client(mcp) as client:
        with pytest.raises(ToolError, match="Only SELECT queries are allowed."):
            query = """DELETE FROM mimer_store.products WHERE product_id = 1"""
            await client.call_tool("execute_query", {"query": query})


@pytest.mark.asyncio
async def test_execute_query_syntax_error(mock_db_connection):
    """Test execution of query with syntax error."""
    async with Client(mcp) as client:
        with pytest.raises(ToolError, match="Syntax error"):
            query = (
                """SELECT product, product_id\nFROM mimer_store.products\nLIMIT 10"""
            )
            await client.call_tool("execute_query", {"query": query})


@pytest.mark.asyncio
async def test_execute_query_no_rows_returned(mock_db_connection):
    """Test execution of query with SELECT returning no rows."""
    async with Client(mcp) as client:
        query = """
                SELECT t.item_id, t.authors_list, t.isbn, p.product
                FROM mimer_store_book.titles t
                JOIN mimer_store.items i ON t.item_id = i.item_id
                JOIN mimer_store.products p ON i.product_id = p.product_id
                WHERE t.authors_list LIKE '%unknown_author%'
                """
        result = await client.call_tool("execute_query", {"query": query})
    assert isinstance(result.data, list)
    assert len(result.data) == 0


@pytest.mark.asyncio
async def test_execute_query_with_param(mock_db_connection):
    """Test execution of query with parameters."""
    async with Client(mcp) as client:
        query = """
                SELECT t.item_id, t.authors_list, t.isbn, p.product
                FROM mimer_store_book.titles t
                JOIN mimer_store.items i ON t.item_id = i.item_id
                JOIN mimer_store.products p ON i.product_id = p.product_id
                WHERE t.authors_list LIKE ?
                """
        params = ["%Rowling%"]
        result = await client.call_tool(
            "execute_query", {"query": query, "params": params}
        )
        # Access the actual result data from structured_content
        actual_data = result.structured_content["result"]
        assert isinstance(actual_data, list)
        assert len(actual_data) == 10
        # Verify all rows contain "Rowling" in authors_list
        for row in actual_data:
            assert "Rowling" in row["authors_list"]


@pytest.mark.asyncio
async def test_execute_query_large_result_set(mock_db_connection):
    """Test execution of query returning a large result set."""
    async with Client(mcp) as client:
        query = """
                SELECT * FROM mimer_store_music.tracks
                """
        result = await client.call_tool("execute_query", {"query": query})
        assert isinstance(result.data, list)
        assert len(result.data) == 8624


@pytest.mark.asyncio
async def test_list_stored_procedures_success(mock_db_connection):
    """Test successful listing of stored procedures."""
    async with Client(mcp) as client:
        result = await client.call_tool("list_stored_procedures")
    assert isinstance(result.data, list)
    assert len(result.data) > 0
    assert len(result.data) == 8


@pytest.mark.asyncio
async def test_get_stored_procedures_definition_success(mock_db_connection):
    """Test successful retrieval of stored procedure definitions."""
    async with Client(mcp) as client:
        result = await client.call_tool(
            "get_stored_procedure_definition",
            {"procedure_schema": "mimer_store", "procedure_name": "barcode"},
        )
    assert isinstance(result.data, str)
    assert "CREATE PROCEDURE barcode" in result.data


@pytest.mark.asyncio
async def test_get_stored_procedures_definition_failure_non_existent_name(
    mock_db_connection,
):
    """Test retrieval of stored procedure definition with non-existent procedure name."""
    async with Client(mcp) as client:
        with pytest.raises(
            ToolError,
            match="Stored procedure name 'non_existent_procedure' does not exist in any schema",
        ):
            await client.call_tool(
                "get_stored_procedure_definition",
                {
                    "procedure_schema": "mimer_store",
                    "procedure_name": "non_existent_procedure",
                },
            )


@pytest.mark.asyncio
async def test_get_stored_procedures_definition_failure_non_existent_schema(
    mock_db_connection,
):
    """Test retrieval of stored procedure definition with non-existent schema."""
    async with Client(mcp) as client:
        with pytest.raises(
            ToolError,
            match="Schema 'non_existent_schema' does not exist",
        ):
            await client.call_tool(
                "get_stored_procedure_definition",
                {
                    "procedure_schema": "non_existent_schema",
                    "procedure_name": "barcode",
                },
            )


@pytest.mark.asyncio
async def test_get_stored_procedures_definition_failure_non_existent_procedure(
    mock_db_connection,
):
    """Test retrieval of stored procedure definition with procedure that does not exist in the given schema."""
    async with Client(mcp) as client:
        with pytest.raises(
            ToolError,
            match="Stored procedure 'search' does not exist in schema 'mimer_store'",
        ):
            await client.call_tool(
                "get_stored_procedure_definition",
                {
                    "procedure_schema": "mimer_store",
                    "procedure_name": "search",
                },
            )


@pytest.mark.asyncio
async def test_get_stored_procedures_definition_failure_syntax_error(
    mock_db_connection,
):
    """Test execution of query with syntax error."""
    async with Client(mcp) as client:
        with pytest.raises(ToolError, match="Syntax error"):
            query = (
                """SELECT product, product_id\nFROM mimer_store.products\nLIMIT 10"""
            )
            await client.call_tool("execute_query", {"query": query})


@pytest.mark.asyncio
async def test_get_stored_procedures_parameters_success(mock_db_connection):
    """Test successful retrieval of stored procedure parameters."""
    async with Client(mcp) as client:
        result = await client.call_tool(
            "get_stored_procedure_parameters",
            {"procedure_schema": "mimer_store", "procedure_name": "barcode"},
        )
    assert isinstance(result.data, dict)
    assert len(result.data) == 3
    assert result.data["parameters"][0] == {
        "p_ean": {"data_type": "BIGINT", "direction": "IN", "default_value": None}
    }


@pytest.mark.asyncio
async def test_execute_stored_procedure_success(mock_db_connection):
    """Test successful execution of stored procedure."""
    async with Client(mcp) as client:
        # Valid JSON object
        result = await client.call_tool(
            "execute_stored_procedure",
            {
                "procedure_schema": "mimer_store",
                "procedure_name": "barcode",
                "parameters": '{"p_ean": 77774238724}',
            },
        )
        assert isinstance(result.data, dict)
        assert result.data["message"] == "Executed mimer_store.barcode successfully."
        assert result.data["result"] == [
            {
                "title": "100 Anos",
                "creator": "Carlos Gardel",
                "format": "Audio CD",
                "price": "9.98",
                "item_id": 60001,
            }
        ]
        # Verify that parameter name case sensitivity does not affect the result
        case_sensitive_result = await client.call_tool(
            "execute_stored_procedure",
            {
                "procedure_schema": "mimer_store",
                "procedure_name": "barcode",
                "parameters": '{"P_EAN": 77774238724}',
            },
        )
        assert case_sensitive_result.data == result.data


@pytest.mark.asyncio
async def test_execute_stored_procedure_failure_none_parameters(mock_db_connection):
    """Test execution of stored procedure with no parameters."""
    async with Client(mcp) as client:
        with pytest.raises(ToolError, match="Parameters JSON string is required"):
            await client.call_tool(
                "execute_stored_procedure",
                {
                    "procedure_schema": "mimer_store",
                    "procedure_name": "barcode",
                    "parameters": "",
                },
            )


@pytest.mark.asyncio
async def test_execute_stored_procedure_failure_invalid_json_parameters(
    mock_db_connection,
):
    """Test execution of stored procedure with invalid JSON for parameters."""
    async with Client(mcp) as client:
        with pytest.raises(
            ToolError,
            match="Invalid JSON for parameters",
        ):
            await client.call_tool(
                "execute_stored_procedure",
                {
                    "procedure_schema": "mimer_store",
                    "procedure_name": "barcode",
                    "parameters": '{key: "value"}',  # Missing quotes around key
                },
            )


@pytest.mark.asyncio
async def test_execute_stored_procedure_unknown_param(
    mock_db_connection,
):
    """Test execution of stored procedure with unknown parameters."""
    async with Client(mcp) as client:
        with pytest.raises(
            ToolError,
            match="Unknown parameter.*unknown_param.*Expected one of",
        ):
            await client.call_tool(
                "execute_stored_procedure",
                {
                    "procedure_schema": "mimer_store",
                    "procedure_name": "barcode",
                    "parameters": '{"unknown_param": "value"}',  # Unknown parameter
                },
            )


@pytest.mark.asyncio
async def test_execute_stored_procedure_conversion_success(
    mock_db_connection,
):
    """Test success execution of stored procedure with type conversions."""
    async with Client(mcp) as client:
        # Success INT conversion from string
        result = await client.call_tool(
            "execute_stored_procedure",
            {
                "procedure_schema": "mimer_store",
                "procedure_name": "barcode",
                "parameters": '{"p_ean": 77774238724}',
            },
        )
        assert isinstance(result.data, dict)
        assert result.data["message"] == "Executed mimer_store.barcode successfully."
        assert result.data["result"] == [
            {
                "title": "100 Anos",
                "creator": "Carlos Gardel",
                "format": "Audio CD",
                "price": "9.98",
                "item_id": 60001,
            }
        ]

        # Success CHARACTER VARYING conversion from string
        result_char = await client.call_tool(
            "execute_stored_procedure",
            {
                "procedure_schema": "mimer_store_book",
                "procedure_name": "search",
                "parameters": '{"p_book_title": "Harry Potter", "p_author": "Rowling"}',
            },
        )

        assert (
            result_char.data["message"]
            == "Executed mimer_store_book.search successfully."
        )
        # Access the actual result data from structured_content
        actual_data = result_char.structured_content["result"]
        assert isinstance(actual_data, list)
        for row in actual_data:
            assert "Rowling" in row["authors_list"]

        # TODO: test DATE, TIME, TIMESTAMP, FLOAT, BOOLEAN conversions


@pytest.mark.asyncio
async def test_execute_stored_procedure_invalid_data_type(
    mock_db_connection,
):
    """Test execution of stored procedure with invalid data type."""
    async with Client(mcp) as client:
        # missing 'p_RecordedBy' required parameter
        with pytest.raises(
            ToolError,
            match="Parameter.*expects.*but got 'invalid_type'.",
        ):
            await client.call_tool(
                "execute_stored_procedure",
                {
                    "procedure_schema": "mimer_store",
                    "procedure_name": "barcode",
                    "parameters": '{"p_ean": "invalid_type"}',
                },
            )


@pytest.mark.asyncio
async def test_execute_stored_procedure_missing_required_parameter(
    mock_db_connection,
):
    """Test execution of stored procedure with missing required parameter."""
    async with Client(mcp) as client:
        # missing 'p_RecordedBy' required parameter
        with pytest.raises(
            ToolError,
            match="Parameter.*is required or non-trailing default cannot be omitted.",
        ):
            await client.call_tool(
                "execute_stored_procedure",
                {
                    "procedure_schema": "mimer_store_music",
                    "procedure_name": "Search",
                    "parameters": '{"p_MusicTitle": "Cumparsita"}',
                },
            )


# TODO: validate missing required parameters up to the last provided index
# TODO: test empty JSON object {} is allowed (for procedures with no parameters) -- need mock procedure with no parameters
# TODO: test execute_stored_procedure tool: failure with non value-pair objects
