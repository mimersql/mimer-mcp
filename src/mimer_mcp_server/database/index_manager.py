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

import logging

from mimer_mcp_server.utils import quote_ident

logger = logging.getLogger(__name__)


class IndexManager:
    """Class for managing indexes in the database"""

    def __init__(self, connection):
        self.connection = connection

    def list_indexes(self, schema: str) -> bool:
        """List all indexes in the specified schema"""
        logger.debug(f"List indexes from schema: {schema}")
        with self.connection.cursor() as cursor:
            # INFORMATION_SCHEMA.EXT_ACCESS_PATHS view shows all explicit and implicit indexes
            # on tables that are accessible by the current ident. All columns in the indexes are 
            # displayed including the primary key columns that are automatically appended to an index.
            
            # INFORMATION_SCHEMA.EXT_INDEXES view shows secondary indexes defined on tables 
            # that are accessible by the current ident.
            
            # INFORMATION_SCHEMA.EXT_INDEX_COLUMN_USAGE view shows on which table columns an secondary index 
            # is defined. Only indexes defined on table accessible by the current ident is shown.
            
            # We will use EXT_ACCESS_PATHS to get all indexes including implicit ones.
            # INDEX_SCHEMA col contains the schema name.
            # INDEX_NAME col contains the index name for the secondary indexes. For implicit indexes,
            # this is the name of the constraint that is the reason for the index, e.g. primary key, unique key, etc.
            # TABLE_NAME col contains the table name on which the index is defined.
            # INDEX_TYPE col contains the type of index; one of FOREIGN KEY, INDEX, INTERNAL KEY, PRIMARY KEY, UNIQUE, UNIQUE INDEX.
            # COLUMN_NAME col contains the column name in the index.
            
            query = """
            SELECT INDEX_NAME, TABLE_NAME, INDEX_TYPE, COLUMN_NAME
            FROM INFORMATION_SCHEMA.EXT_ACCESS_PATHS
            WHERE INDEX_SCHEMA = ?
            ORDER BY TABLE_NAME, INDEX_NAME
            """
            
            cursor.execute(query, (schema,))
            result = cursor.fetchall()
            indexes = []
            for row in result:
                indexes.append({
                    "index_name": row[0],
                    "table_name": row[1],
                    "index_type": row[2],
                    "column_name": row[3],
                })
            return indexes
        
    def create_index(self, schema: str, table: str, index_name: str, columns: list) -> None:
        """Create an index on the specified table and columns"""
        logger.debug(f"Create index {index_name} on {schema}.{table}({', '.join(columns)})")
        quoted_cols = ", ".join(quote_ident(c) for c in columns)
        sql = f'CREATE INDEX {quote_ident(index_name)} ON {quote_ident(schema)}.{quote_ident(table)} ({quoted_cols})'
        with self.connection.cursor() as cursor:
            cursor.execute(sql)
        self.connection.commit()

# test code for IndexManager
if __name__ == "__main__":
    from mimer_mcp_server.database.connection import init_db_pool, get_connection, close_db_pool

    # Initialize the database connection pool
    init_db_pool()
    try:
        # Get a connection from the pool
        conn = get_connection()
        index_manager = IndexManager(conn)
        indexes = index_manager.list_indexes("admin")
        print("Indexes:", indexes)
    finally:
        # Close the database connection pool
        close_db_pool()