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
from unittest.mock import MagicMock, patch
import subprocess
from mimer_mcp_server.database import monitoring


class TestGetMiminfoStats:
    """Test suite for get_miminfo_stats function."""

    def test_get_miminfo_stats_success(self):
        """Test successful retrieval of miminfo statistics."""
        expected_output = (
            "General Statistics:\n  Transactions: 100\n  Pages Used: 5000\n"
        )

        mock_result = MagicMock()
        mock_result.stdout = expected_output

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            result = monitoring.get_miminfo_stats()

            assert result == expected_output
            mock_run.assert_called_once_with(
                [
                    "miminfo",
                    "-p",
                    monitoring.DB_CONFIG["dsn"],
                ],
                capture_output=True,
                text=True,
            )

    def test_get_miminfo_stats_with_real_output(self):
        """Test retrieval with realistic miminfo output format."""
        realistic_output = """Mimer SQL Version 11.0
            General Statistics:
            Current Transactions: 5
            Committed Transactions: 1000
            Rolled Back Transactions: 50
            Page Management:
            Total Pages: 10000
            Used Pages: 7500
            """
        mock_result = MagicMock()
        mock_result.stdout = realistic_output

        with patch("subprocess.run", return_value=mock_result):
            result = monitoring.get_miminfo_stats()

            assert "General Statistics" in result
            assert "Page Management" in result
            assert "Total Pages" in result

    def test_get_miminfo_stats_empty_output(self):
        """Test handling of empty output from miminfo."""
        mock_result = MagicMock()
        mock_result.stdout = ""

        with patch("subprocess.run", return_value=mock_result):
            result = monitoring.get_miminfo_stats()

            assert result == ""

    def test_get_miminfo_stats_subprocess_error(self):
        """Test error handling when miminfo command fails."""
        error_message = "Database connection failed"

        with patch(
            "subprocess.run",
            side_effect=subprocess.CalledProcessError(
                1, "miminfo", stderr=error_message
            ),
        ):
            with pytest.raises(
                RuntimeError, match="Failed to retrieve Mimer SQL stats"
            ):
                monitoring.get_miminfo_stats()

    def test_get_miminfo_stats_subprocess_error_logs(self, caplog):
        """Test that subprocess errors are properly logged."""
        error_message = "Connection timeout"

        with patch(
            "subprocess.run",
            side_effect=subprocess.CalledProcessError(
                1, "miminfo", stderr=error_message
            ),
        ):
            with pytest.raises(RuntimeError):
                monitoring.get_miminfo_stats()

            # Verify error was logged
            assert "Failed to retrieve Mimer SQL stats" in caplog.text

    def test_get_miminfo_stats_calls_correct_command(self):
        """Test that the correct miminfo command is called with right parameters."""
        mock_result = MagicMock()
        mock_result.stdout = "test output"

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            monitoring.get_miminfo_stats()

            # Verify the command and arguments
            call_args = mock_run.call_args
            command = call_args[0][0]

            assert command[0] == "miminfo"
            assert command[1] == "-p"
            assert command[2] == monitoring.DB_CONFIG["dsn"]


class TestGetSqlmonitorStats:
    """Test suite for get_sqlmonitor_stats function."""

    def test_get_sqlmonitor_stats_success(self):
        """Test successful retrieval of sqlmonitor statistics."""
        expected_output = (
            "SQL Monitor Statistics:\n  Active Queries: 5\n  Top Query: SELECT ...\n"
        )

        mock_result = MagicMock()
        mock_result.stdout = expected_output

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            result = monitoring.get_sqlmonitor_stats()

            assert result == expected_output
            mock_run.assert_called_once_with(
                [
                    "sqlmonitor",
                    monitoring.DB_CONFIG["dsn"],
                    "-u",
                    monitoring.DB_CONFIG["user"],
                    "-p",
                    monitoring.DB_CONFIG["password"],
                ],
                capture_output=True,
                text=True,
            )

    def test_get_sqlmonitor_stats_with_real_output(self):
        """Test retrieval with realistic sqlmonitor output format."""
        realistic_output = """SQL Monitor Report
        Session     User        SQL Text                    Elapsed Time
        1           MIMER_STORE SELECT COUNT(*) FROM MAIN  0.123s
        2           MIMER_STORE INSERT INTO LOG VALUES     0.045s
        3           MIMER_STORE UPDATE STATS SET ...       0.089s
        """
        mock_result = MagicMock()
        mock_result.stdout = realistic_output

        with patch("subprocess.run", return_value=mock_result):
            result = monitoring.get_sqlmonitor_stats()

            assert "SQL Monitor Report" in result
            assert "Session" in result
            assert "Elapsed Time" in result

    def test_get_sqlmonitor_stats_empty_output(self):
        """Test handling of empty output from sqlmonitor."""
        mock_result = MagicMock()
        mock_result.stdout = ""

        with patch("subprocess.run", return_value=mock_result):
            result = monitoring.get_sqlmonitor_stats()

            assert result == ""

    def test_get_sqlmonitor_stats_subprocess_error(self):
        """Test error handling when sqlmonitor command fails."""
        error_message = "Authentication failed"

        with patch(
            "subprocess.run",
            side_effect=subprocess.CalledProcessError(
                1, "sqlmonitor", stderr=error_message
            ),
        ):
            with pytest.raises(
                RuntimeError, match="Failed to retrieve sqlmonitor stats"
            ):
                monitoring.get_sqlmonitor_stats()

    def test_get_sqlmonitor_stats_subprocess_error_logs(self, caplog):
        """Test that subprocess errors are properly logged."""
        error_message = "Invalid credentials"

        with patch(
            "subprocess.run",
            side_effect=subprocess.CalledProcessError(
                1, "sqlmonitor", stderr=error_message
            ),
        ):
            with pytest.raises(RuntimeError):
                monitoring.get_sqlmonitor_stats()

            # Verify error was logged
            assert "Failed to retrieve sqlmonitor stats" in caplog.text

    def test_get_sqlmonitor_stats_calls_correct_command(self):
        """Test that the correct sqlmonitor command is called with right parameters."""
        mock_result = MagicMock()
        mock_result.stdout = "test output"

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            monitoring.get_sqlmonitor_stats()

            # Verify the command and arguments
            call_args = mock_run.call_args
            command = call_args[0][0]

            assert command[0] == "sqlmonitor"
            assert command[1] == monitoring.DB_CONFIG["dsn"]
            assert command[2] == "-u"
            assert command[3] == monitoring.DB_CONFIG["user"]
            assert command[4] == "-p"
            assert command[5] == monitoring.DB_CONFIG["password"]

    def test_get_sqlmonitor_stats_with_credentials(self, monkeypatch):
        """Test that sqlmonitor uses correct credentials from DB_CONFIG."""
        test_dsn = "test_database"
        test_user = "test_user"
        test_password = "test_password"

        # Mock subprocess.run
        mock_result = MagicMock()
        mock_result.stdout = "output"

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            # Temporarily override DB_CONFIG for this test
            original_config = monitoring.DB_CONFIG.copy()
            monitoring.DB_CONFIG["dsn"] = test_dsn
            monitoring.DB_CONFIG["user"] = test_user
            monitoring.DB_CONFIG["password"] = test_password

            try:
                monitoring.get_sqlmonitor_stats()

                # Verify correct credentials were passed
                call_args = mock_run.call_args[0][0]
                assert test_dsn in call_args
                assert test_user in call_args
                assert test_password in call_args
            finally:
                # Restore original config
                monitoring.DB_CONFIG.update(original_config)


class TestMonitoringIntegration:
    """Integration-level tests for monitoring functions."""

    def test_both_functions_handle_capture_output(self):
        """Test that both functions use capture_output=True."""
        mock_result = MagicMock()
        mock_result.stdout = "output"

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            monitoring.get_miminfo_stats()

            assert mock_run.call_args[1]["capture_output"] is True
            assert mock_run.call_args[1]["text"] is True

        mock_run.reset_mock()

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            monitoring.get_sqlmonitor_stats()

            assert mock_run.call_args[1]["capture_output"] is True
            assert mock_run.call_args[1]["text"] is True

    def test_both_functions_return_string(self):
        """Test that both functions return strings."""
        mock_result = MagicMock()
        mock_result.stdout = "test output"

        with patch("subprocess.run", return_value=mock_result):
            result1 = monitoring.get_miminfo_stats()
            result2 = monitoring.get_sqlmonitor_stats()

            assert isinstance(result1, str)
            assert isinstance(result2, str)

    def test_both_functions_raise_runtime_error_on_failure(self):
        """Test that both functions raise RuntimeError on subprocess failure."""
        with patch(
            "subprocess.run", side_effect=subprocess.CalledProcessError(1, "cmd")
        ):
            with pytest.raises(RuntimeError):
                monitoring.get_miminfo_stats()

        with patch(
            "subprocess.run", side_effect=subprocess.CalledProcessError(1, "cmd")
        ):
            with pytest.raises(RuntimeError):
                monitoring.get_sqlmonitor_stats()


class TestGetQueryPlan:
    """Test suite for get_query_plan function."""

    def test_get_query_plan_success(self):
        """Test successful query plan retrieval."""
        query = "SELECT * FROM table1"
        plan_xml = "<QueryPlan><Operation>TableScan</Operation></QueryPlan>"
        bsql_output = f"Start of explain result\n{plan_xml}\nEnd of explain result"

        mock_result = MagicMock()
        mock_result.stdout = bsql_output
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result):
            with patch("builtins.open", create=True):
                result = monitoring.get_query_plan(query)

                assert result["success"] is True
                assert result["plan"] == plan_xml
                assert result["error"] is None

    def test_get_query_plan_with_query_without_semicolon(self):
        """Test query plan retrieval for query without trailing semicolon."""
        query = "SELECT COUNT(*) FROM users"
        plan_xml = "<QueryPlan><Operation>Aggregate</Operation></QueryPlan>"
        bsql_output = f"Start of explain result\n{plan_xml}\nEnd of explain result"

        mock_result = MagicMock()
        mock_result.stdout = bsql_output
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            with patch("builtins.open", create=True):
                monitoring.get_query_plan(query)

                # Verify subprocess was called with bsql command
                call_args = mock_run.call_args
                command = call_args[0][0]
                assert command[0] == "bsql"

    def test_get_query_plan_with_query_with_semicolon(self):
        """Test query plan retrieval for query with trailing semicolon."""
        query = "SELECT * FROM products;"
        plan_xml = "<QueryPlan><Operation>FullTableScan</Operation></QueryPlan>"
        bsql_output = f"Start of explain result\n{plan_xml}\nEnd of explain result"

        mock_result = MagicMock()
        mock_result.stdout = bsql_output
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result):
            with patch("builtins.open", create=True):
                result = monitoring.get_query_plan(query)

                assert result["success"] is True
                assert result["plan"] == plan_xml

    def test_get_query_plan_bsql_execution_failure(self):
        """Test error handling when BSQL execution fails."""
        query = "SELECT * FROM table1"
        error_output = "Error: Invalid SQL syntax"

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = error_output

        with patch("subprocess.run", return_value=mock_result):
            with patch("builtins.open", create=True):
                result = monitoring.get_query_plan(query)

                assert result["success"] is False
                assert result["plan"] is None
                assert "BSQL execution failed" in result["error"]
                assert result["stderr"] == error_output

    def test_get_query_plan_timeout(self):
        """Test timeout handling in query plan retrieval."""
        query = "SELECT * FROM large_table"

        with patch(
            "subprocess.run",
            side_effect=subprocess.TimeoutExpired("bsql", 1800),
        ):
            with patch("builtins.open", create=True):
                result = monitoring.get_query_plan(query)

                assert result["success"] is False
                assert result["plan"] is None
                assert "timed out" in result["error"].lower()

    def test_get_query_plan_no_explain_plan_found(self):
        """Test handling when no explain plan is found in output."""
        query = "SELECT * FROM table1"
        bsql_output = "Some output without explain markers"

        mock_result = MagicMock()
        mock_result.stdout = bsql_output
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result):
            with patch("builtins.open", create=True):
                result = monitoring.get_query_plan(query)

                assert result["success"] is False
                assert result["plan"] is None
                assert "No explain plan found" in result["error"]

    def test_get_query_plan_exception_handling(self):
        """Test generic exception handling."""
        query = "SELECT * FROM table1"

        with patch("subprocess.run", side_effect=Exception("Unexpected error")):
            with patch("builtins.open", create=True):
                result = monitoring.get_query_plan(query)

                assert result["success"] is False
                assert result["plan"] is None
                assert "Unexpected error" in result["error"]

    def test_get_query_plan_bsql_command_format(self):
        """Test that BSQL command is formatted correctly."""
        query = "SELECT 1"

        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            with patch("builtins.open", create=True):
                monitoring.get_query_plan(query)

                call_args = mock_run.call_args
                command = call_args[0][0]

                # Verify command structure: bsql -u <user> -p <password> <dsn>
                assert command[0] == "bsql"
                assert command[1] == "-u"
                assert command[2] == monitoring.DB_CONFIG["user"]
                assert command[3] == "-p"
                assert command[4] == monitoring.DB_CONFIG["password"]
                assert command[5] == monitoring.DB_CONFIG["dsn"]

    def test_get_query_plan_multiline_query(self):
        """Test query plan with multiline SQL query."""
        query = """SELECT customer_id, COUNT(*) as order_count
                   FROM orders
                   WHERE date > '2024-01-01'
                   GROUP BY customer_id"""
        plan_xml = "<QueryPlan><Operation>GroupBy</Operation></QueryPlan>"
        bsql_output = f"Start of explain result\n{plan_xml}\nEnd of explain result"

        mock_result = MagicMock()
        mock_result.stdout = bsql_output
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result):
            with patch("builtins.open", create=True):
                result = monitoring.get_query_plan(query)

                assert result["success"] is True
                assert result["plan"] == plan_xml

    def test_get_query_plan_complex_xml_plan(self):
        """Test extraction of complex XML query plan."""
        query = "SELECT * FROM table1"
        plan_xml = """<QueryPlan>
  <Operation type="Join">
    <Method>NestedLoopJoin</Method>
    <LeftChild>
      <Operation type="TableScan">
        <Table>table1</Table>
      </Operation>
    </LeftChild>
    <RightChild>
      <Operation type="IndexSeek">
        <Index>idx_table2</Index>
      </Operation>
    </RightChild>
  </Operation>
</QueryPlan>"""
        bsql_output = f"Some preamble\nStart of explain result\n{plan_xml}\nEnd of explain result\nSome epilog"

        mock_result = MagicMock()
        mock_result.stdout = bsql_output
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result):
            with patch("builtins.open", create=True):
                result = monitoring.get_query_plan(query)

                assert result["success"] is True
                assert plan_xml in result["plan"]


class TestExtractExplainPlan:
    """Test suite for _extract_explain_plan helper function."""

    def test_extract_explain_plan_simple(self):
        """Test extracting simple explain plan."""
        plan_xml = "<QueryPlan><Operation>Scan</Operation></QueryPlan>"
        output = f"Start of explain result\n{plan_xml}\nEnd of explain result"

        result = monitoring._extract_explain_plan(output)

        assert result == plan_xml

    def test_extract_explain_plan_with_whitespace(self):
        """Test extraction with surrounding whitespace."""
        plan_xml = "<QueryPlan><Operation>Join</Operation></QueryPlan>"
        output = f"Start of explain result\n  \n{plan_xml}\n  \nEnd of explain result"

        result = monitoring._extract_explain_plan(output)

        # Should trim whitespace
        assert result == plan_xml

    def test_extract_explain_plan_multiline(self):
        """Test extracting multiline explain plan."""
        plan_xml = """<QueryPlan>
  <Operation>Join</Operation>
</QueryPlan>"""
        output = f"Start of explain result\n{plan_xml}\nEnd of explain result"

        result = monitoring._extract_explain_plan(output)

        assert plan_xml in result

    def test_extract_explain_plan_no_start_marker(self):
        """Test that extraction returns None when start marker is missing."""
        output = "Some output\nEnd of explain result\nMore output"

        result = monitoring._extract_explain_plan(output)

        assert result is None

    def test_extract_explain_plan_no_end_marker(self):
        """Test that extraction returns None when end marker is missing."""
        output = "Some output\nStart of explain result\nMore output"

        result = monitoring._extract_explain_plan(output)

        assert result is None

    def test_extract_explain_plan_empty_output(self):
        """Test extraction with empty output."""
        result = monitoring._extract_explain_plan("")

        assert result is None

    def test_extract_explain_plan_markers_only(self):
        """Test extraction with only markers and no content."""
        output = "Start of explain result\nEnd of explain result"

        result = monitoring._extract_explain_plan(output)

        # Should return empty string or None (whitespace trimmed)
        assert result == "" or result is None

    def test_extract_explain_plan_with_surrounding_text(self):
        """Test extraction with surrounding text and preamble/epilog."""
        plan_xml = "<QueryPlan><Operation>Scan</Operation></QueryPlan>"
        output = f"""BSQL version 11.0
            Connected to database

            Start of explain result
            {plan_xml}
            End of explain result

            Query complete."""

        result = monitoring._extract_explain_plan(output)

        assert result == plan_xml

    def test_extract_explain_plan_duplicate_markers(self):
        """Test extraction when markers appear multiple times (takes first/last)."""

        plan_xml1 = "<QueryPlan>First Plan</QueryPlan>"

        plan_xml2 = "<QueryPlan>Second Plan</QueryPlan>"

        output = f"""Start of explain result
{plan_xml1}
End of explain result
Start of explain result
{plan_xml2}
End of explain result"""

        result = monitoring._extract_explain_plan(output)

        # Should extract between first start and first end
        assert plan_xml1 in result
