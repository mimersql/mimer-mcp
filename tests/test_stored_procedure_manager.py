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

import json
from unittest.mock import MagicMock, patch
from mimer_mcp_server.database.stored_procedure_manager import StoredProcedureManager


def _make_manager(call_rows=None, call_columns=None):
    """Return a StoredProcedureManager with a mocked connection.

    The mock is pre-wired so that _validate_procedure_exists is bypassed
    and get_stored_procedure_parameters returns a single INTEGER IN param.

    Args:
        call_rows: Rows returned by cursor.fetchall() during the CALL execution.
        call_columns: cursor.description for the CALL result (list of (name,) tuples).
    """
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = call_rows or []
    mock_cursor.description = call_columns or [("result",)]
    mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

    manager = StoredProcedureManager(mock_conn)
    return manager, mock_cursor


def _stub_procedure(manager, schema, name, params=None):
    """Patch validation and metadata so execute_stored_procedure can run without a DB."""
    if params is None:
        # Default: one INTEGER IN param named 'p_id' with no default
        params = [{"p_id": {"data_type": "INTEGER", "direction": "IN", "default_value": None}}]

    manager._validate_procedure_exists = MagicMock()
    manager.get_stored_procedure_parameters = MagicMock(
        return_value={
            "procedure_schema": schema,
            "procedure_name": name,
            "parameters": params,
        }
    )


class TestExecuteStoredProcedureCallSQL:
    """Unit tests validating the CALL SQL identifier quoting in execute_stored_procedure."""

    def test_normal_names_produce_quoted_call(self):
        """Standard schema and procedure names should appear double-quoted in CALL."""
        manager, mock_cursor = _make_manager()
        _stub_procedure(manager, "my_schema", "my_proc")

        manager.execute_stored_procedure("my_schema", "my_proc", '{"p_id": 1}')

        sql = mock_cursor.execute.call_args[0][0]
        assert sql == 'CALL "my_schema"."my_proc"(?)'

    def test_schema_with_embedded_double_quote_is_escaped(self):
        """A double quote in the schema name must be escaped as \"\" in CALL."""
        manager, mock_cursor = _make_manager()
        _stub_procedure(manager, 'sch"ema', "my_proc")

        manager.execute_stored_procedure('sch"ema', "my_proc", '{"p_id": 1}')

        sql = mock_cursor.execute.call_args[0][0]
        assert '"sch""ema"' in sql

    def test_procedure_with_embedded_double_quote_is_escaped(self):
        """A double quote in the procedure name must be escaped as \"\" in CALL."""
        manager, mock_cursor = _make_manager()
        _stub_procedure(manager, "s", 'proc"name')

        manager.execute_stored_procedure("s", 'proc"name', '{"p_id": 1}')

        sql = mock_cursor.execute.call_args[0][0]
        assert '"proc""name"' in sql

    def test_call_with_no_parameters_uses_empty_parens(self):
        """A procedure with no params should produce CALL "s"."p"()."""
        manager, mock_cursor = _make_manager()
        _stub_procedure(manager, "s", "p", params=[])

        manager.execute_stored_procedure("s", "p", "{}")

        sql = mock_cursor.execute.call_args[0][0]
        assert sql == 'CALL "s"."p"()'

    def test_call_with_multiple_params_has_correct_placeholders(self):
        """Three IN params should produce CALL "s"."p"(?, ?, ?)."""
        params = [
            {"p_a": {"data_type": "INTEGER", "direction": "IN", "default_value": None}},
            {"p_b": {"data_type": "INTEGER", "direction": "IN", "default_value": None}},
            {"p_c": {"data_type": "INTEGER", "direction": "IN", "default_value": None}},
        ]
        manager, mock_cursor = _make_manager()
        _stub_procedure(manager, "s", "p", params=params)

        manager.execute_stored_procedure("s", "p", '{"p_a": 1, "p_b": 2, "p_c": 3}')

        sql = mock_cursor.execute.call_args[0][0]
        assert sql == 'CALL "s"."p"(?, ?, ?)'

    def test_result_rows_are_returned_as_list_of_dicts(self):
        """Rows from cursor should be returned in the result dict."""
        columns = [("col1",), ("col2",)]
        rows = [("val1", "val2")]
        manager, _ = _make_manager(call_rows=rows, call_columns=columns)
        _stub_procedure(manager, "s", "p")

        result = manager.execute_stored_procedure("s", "p", '{"p_id": 42}')

        assert result["message"] == "Executed s.p successfully."
        assert result["result"] == [{"col1": "val1", "col2": "val2"}]
