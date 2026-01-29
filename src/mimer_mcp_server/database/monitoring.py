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

"""
Mimer SQL Performance Monitoring and Query Analysis Tools

This module provides utilities for monitoring database performance and
analyzing query execution plans using Mimer SQL CLI tools:
- Runtime statistics (miminfo)
- SQL monitoring (sqlmonitor)
- Query execution plan analysis (bsql EXPLAIN)
"""

import logging
import subprocess
import tempfile
import os
from typing import Optional
from mimer_mcp_server import config

logger = logging.getLogger(__name__)

DB_CONFIG = {
    "dsn": config.DB_DSN,
    "user": config.DB_USER,
    "password": config.DB_PASSWORD,
}

# ============================================================================
# Runtime Statistics Monitoring
# ============================================================================


# MIMINFO
def get_miminfo_stats() -> str:
    """Retrieve Mimer SQL runtime statistics using the miminfo CLI tool.

    Returns:
        str: The output of the miminfo command containing runtime statistics.

    Raises:
        RuntimeError: If the miminfo command fails.
    """
    try:
        result = subprocess.run(
            [
                "miminfo",
                "-p",
                DB_CONFIG["dsn"],
            ],
            capture_output=True,
            text=True,
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to retrieve Mimer SQL stats: {e.stderr}")
        raise RuntimeError("Failed to retrieve Mimer SQL stats") from e


# SQLMONITOR
def get_sqlmonitor_stats() -> str:
    """Retrieve SQL monitoring statistics using the sqlmonitor CLI tool.

    Returns:
        str: The output of the sqlmonitor command.

    Raises:
        RuntimeError: If the SQL monitoring command fails.
    """
    try:
        result = subprocess.run(
            [
                "sqlmonitor",
                DB_CONFIG["dsn"],
                "-u",
                DB_CONFIG["user"],
                "-p",
                DB_CONFIG["password"],
            ],
            capture_output=True,
            text=True,
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to retrieve sqlmonitor stats: {e.stderr}")
        raise RuntimeError("Failed to retrieve sqlmonitor stats") from e


# ============================================================================
# Query Execution Plan Analysis
# ============================================================================


def get_query_plan(sql_query: str) -> dict:
    """Get the execution plan for a SQL query using BSQL EXPLAIN.

    This function creates a temporary script file, executes it with bsql,
    and extracts the XML query execution plan.

    Args:
        sql_query: The SQL query to explain

    Returns:
        dict: Contains 'success' boolean, 'plan' with the query plan XML,
              and 'error' message if applicable

    Example:
        >>> result = get_query_plan("SELECT * FROM users WHERE id = 1")
        >>> if result['success']:
        ...     print(result['plan'])  # XML execution plan
    """
    # Create a temporary script file for BSQL
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    ) as script_file:
        script_path = script_file.name

        try:
            # Write BSQL commands following the required format:
            # SET EXPLAIN ON;
            # SET EXECUTE OFF;
            # @
            # <query>;
            # @
            # EXIT
            script_file.write("SET EXPLAIN ON;\n")
            script_file.write("SET EXECUTE OFF;\n")
            script_file.write("\n@\n")
            script_file.write(sql_query)
            if not sql_query.rstrip().endswith(";"):
                script_file.write(";")
            script_file.write("\n@\n")
            script_file.write("\nEXIT\n")
            script_file.flush()

            # Build BSQL command: bsql -u {user} -p {password} {dsn} < script.txt
            bsql_cmd = [
                "bsql",
                "-u",
                DB_CONFIG["user"],
                "-p",
                DB_CONFIG["password"],
                DB_CONFIG["dsn"],
            ]

            # Execute BSQL with input redirection
            with open(script_path, "r", encoding="utf-8") as script_input:
                result = subprocess.run(
                    bsql_cmd,
                    stdin=script_input,
                    capture_output=True,
                    text=True,
                    timeout=120,
                )

            output = result.stdout
            error_output = result.stderr

            # Check for execution errors
            if result.returncode != 0:
                logger.error(f"BSQL execution failed: {error_output}")
                return {
                    "success": False,
                    "plan": None,
                    "error": f"BSQL execution failed with return code {result.returncode}",
                    "stderr": error_output,
                    "stdout": output,
                }

            # Extract the explain plan from output
            plan = _extract_explain_plan(output)

            if plan:
                return {
                    "success": True,
                    "plan": plan,
                    "error": None,
                }
            else:
                logger.warning("No explain plan found in BSQL output")
                return {
                    "success": False,
                    "plan": None,
                    "error": "No explain plan found in BSQL output",
                }

        except subprocess.TimeoutExpired:
            logger.error("BSQL execution timed out")
            return {
                "success": False,
                "plan": None,
                "error": "BSQL execution timed out after 120 seconds",
            }
        except Exception as e:
            logger.error(f"Unexpected error during query plan retrieval: {str(e)}")
            return {
                "success": False,
                "plan": None,
                "error": f"Unexpected error: {str(e)}",
            }
        finally:
            # Clean up the temporary script file
            try:
                os.unlink(script_path)
            except Exception:
                pass


def _extract_explain_plan(output: str) -> Optional[str]:
    """Extract the XML explain plan from BSQL output.

    The explain plan is between "Start of explain result" and
    "End of explain result" markers in the BSQL output.

    Args:
        output: Raw BSQL output

    Returns:
        The extracted XML plan, or None if not found
    """
    start_marker = "Start of explain result"
    end_marker = "End of explain result"

    try:
        start_idx = output.find(start_marker)
        if start_idx == -1:
            return None

        # Move past the start marker and newline
        start_idx = output.find("\n", start_idx) + 1

        end_idx = output.find(end_marker, start_idx)
        if end_idx == -1:
            return None

        # Extract the plan (trim whitespace)
        plan = output[start_idx:end_idx].strip()
        return plan

    except Exception:
        return None
