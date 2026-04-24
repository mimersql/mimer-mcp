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
from mimer_mcp_server.utils import quote_ident
from mimer_mcp_server.database.index_manager import IndexManager


class TestQuoteIdent:
    """Tests for the quote_ident utility function."""

    def test_simple_identifier(self):
        assert quote_ident("my_table") == '"my_table"'

    def test_identifier_with_embedded_double_quote(self):
        assert quote_ident('table"name') == '"table""name"'

    def test_identifier_with_multiple_double_quotes(self):
        assert quote_ident('a"b"c') == '"a""b""c"'

    def test_empty_string(self):
        assert quote_ident("") == '""'

    def test_identifier_with_spaces(self):
        assert quote_ident("my table") == '"my table"'

    def test_identifier_with_semicolon(self):
        """Semicolons are safely contained within double quotes."""
        assert quote_ident("x; DROP TABLE users --") == '"x; DROP TABLE users --"'


class TestCreateIndex:
    """Tests for IndexManager.create_index SQL construction."""

    def _make_manager(self):
        """Create an IndexManager with a mocked connection."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        return IndexManager(mock_conn), mock_cursor, mock_conn

    def test_simple_create_index(self):
        manager, mock_cursor, mock_conn = self._make_manager()
        manager.create_index("my_schema", "my_table", "idx_col1", ["col1"])

        sql = mock_cursor.execute.call_args[0][0]
        assert sql == 'CREATE INDEX "idx_col1" ON "my_schema"."my_table" ("col1")'
        mock_conn.commit.assert_called_once()

    def test_multi_column_index(self):
        manager, mock_cursor, _ = self._make_manager()
        manager.create_index("s", "t", "idx_multi", ["col1", "col2", "col3"])

        sql = mock_cursor.execute.call_args[0][0]
        assert sql == 'CREATE INDEX "idx_multi" ON "s"."t" ("col1", "col2", "col3")'

    def test_injection_via_index_name_with_semicolon(self):
        """A semicolon in the index name is safely quoted, not executed as a statement separator."""
        manager, mock_cursor, _ = self._make_manager()
        manager.create_index("s", "t", "x; DROP TABLE users --", ["col1"])

        sql = mock_cursor.execute.call_args[0][0]
        assert sql == 'CREATE INDEX "x; DROP TABLE users --" ON "s"."t" ("col1")'
        assert "DROP TABLE" not in sql.split('"x; DROP TABLE users --"')[0]

    def test_injection_via_double_quote_in_table_name(self):
        """A double quote in the table name is escaped, preventing breakout."""
        manager, mock_cursor, _ = self._make_manager()
        manager.create_index("s", 'tab"le', "idx", ["col1"])

        sql = mock_cursor.execute.call_args[0][0]
        assert sql == 'CREATE INDEX "idx" ON "s"."tab""le" ("col1")'

    def test_injection_via_column_name(self):
        """Malicious column names are safely quoted."""
        manager, mock_cursor, _ = self._make_manager()
        manager.create_index("s", "t", "idx", ['col1"); DROP TABLE x --'])

        sql = mock_cursor.execute.call_args[0][0]
        assert '"col1""); DROP TABLE x --"' in sql
