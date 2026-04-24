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

from unittest.mock import MagicMock
from mimer_mcp_server.database.schema_inspector import SchemaInspector


def _make_inspector(rows=None, columns=None):
    """Return a SchemaInspector backed by a mocked connection.

    Args:
        rows: List of tuples returned by fetchall (default: empty list).
        columns: Cursor description tuples, e.g. [("col1",), ("col2",)].
    """
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = rows or []
    mock_cursor.description = columns or [("id",), ("name",)]
    mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    return SchemaInspector(mock_conn), mock_cursor


class TestGetSampleRows:
    """Unit tests for SchemaInspector._get_sample_rows SQL construction."""

    def test_identifiers_are_quoted_in_sql(self):
        """Schema and table name should appear double-quoted in the SQL."""
        inspector, mock_cursor = _make_inspector()
        # Signature: _get_sample_rows(table_name, schema, limit)
        inspector._get_sample_rows("my_table", "my_schema", limit=3)

        sql = mock_cursor.execute.call_args.args[0]
        assert '"my_schema"."my_table"' in sql

    def test_limit_is_a_bind_parameter(self):
        """limit must be passed as a bind parameter, not interpolated."""
        inspector, mock_cursor = _make_inspector()
        inspector._get_sample_rows("t", "s", limit=5)

        args = mock_cursor.execute.call_args.args
        sql = args[0]
        bind_params = args[1]
        # The SQL should contain a placeholder, not the literal number
        assert "?" in sql
        assert "5" not in sql
        # The bind parameters tuple must contain the limit value
        assert bind_params == (5,)

    def test_default_limit_is_bound_as_parameter(self):
        """Default limit of 3 should also be a bind parameter."""
        inspector, mock_cursor = _make_inspector()
        inspector._get_sample_rows("t", "s")

        bind_params = mock_cursor.execute.call_args.args[1]
        assert bind_params == (3,)

    def test_schema_with_embedded_double_quote_is_escaped(self):
        """A double quote inside the schema name must be escaped as \"\"."""
        inspector, mock_cursor = _make_inspector()
        inspector._get_sample_rows("t", 'sch"ema', limit=1)

        sql = mock_cursor.execute.call_args.args[0]
        assert '"sch""ema"' in sql
        # Raw unescaped form must not appear
        assert '"sch"ema"' not in sql.replace('"sch""ema"', "")

    def test_table_with_embedded_double_quote_is_escaped(self):
        """A double quote inside the table name must be escaped as \"\"."""
        inspector, mock_cursor = _make_inspector()
        inspector._get_sample_rows('tab"le', "s", limit=1)

        sql = mock_cursor.execute.call_args.args[0]
        assert '"tab""le"' in sql

    def test_returns_list_of_dicts(self):
        """Result should be a list of dicts keyed by column names."""
        columns = [("id",), ("name",)]
        rows = [(1, "Alice"), (2, "Bob")]
        inspector, _ = _make_inspector(rows=rows, columns=columns)

        result = inspector._get_sample_rows("s", "t", limit=2)

        assert result == [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]

    def test_returns_empty_list_when_no_rows(self):
        inspector, _ = _make_inspector(rows=[], columns=[("id",)])
        result = inspector._get_sample_rows("s", "t")
        assert result == []
