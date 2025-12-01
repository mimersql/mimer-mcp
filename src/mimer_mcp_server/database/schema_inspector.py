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
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class SchemaInspector:
    """Class for inspecting database schema information.

    This class provides methods to retrieve detailed information about
    database schemas, tables, columns, constraints, and sample data from
    a Mimer SQL database.
    """

    def __init__(self, connection):
        self.connection = connection

    def schema_exists(self, schema: str) -> bool:
        """Check if a schema exists by name."""
        logger.debug(f"Checking if schema exists: {schema}")
        with self.connection.cursor() as cursor:
            query = """
                SELECT CASE WHEN EXISTS (
                    SELECT 1 FROM INFORMATION_SCHEMA.SCHEMATA
                    WHERE SCHEMA_NAME = ?
                ) THEN 1 ELSE 0 END
                FROM SYSTEM.ONEROW
            """
            cursor.execute(query, (schema,))
            row = cursor.fetchone()
            return bool(row and row[0] == 1)

    def _get_columns(self, table: str, schema: str) -> list[Dict[str, Any]]:
        """Get column information for a given table in a schema.

        Returns:
            List of dicts with column info: {name, data_type, is_nullable, character_maximum_length, numeric_precision, numeric_scale, datetime_precision}
        """
        logger.debug(f"Retrieving column info for {schema}.{table}")

        with self.connection.cursor() as cursor:
            # TODO: Add INTERVAL_TYPE, INTERVAL_PRECISION to support INTERVAL data type
            query = (
                "SELECT c.COLUMN_NAME, c.DATA_TYPE, c.COLUMN_DEFAULT, c.IS_NULLABLE, "
                "c.CHARACTER_MAXIMUM_LENGTH, c.NUMERIC_PRECISION, c.NUMERIC_SCALE, c.DATETIME_PRECISION, r.REMARKS "
                "FROM INFORMATION_SCHEMA.COLUMNS c "
                "LEFT JOIN INFORMATION_SCHEMA.EXT_COLUMN_REMARKS r "
                "ON r.TABLE_SCHEMA = c.TABLE_SCHEMA AND r.TABLE_NAME = c.TABLE_NAME AND r.COLUMN_NAME = c.COLUMN_NAME "
                "WHERE c.TABLE_NAME = ? AND c.TABLE_SCHEMA = ? "
                "ORDER BY c.ORDINAL_POSITION"
            )

            cursor.execute(query, (table, schema))
            columns = cursor.fetchall()

            logger.debug(f"Retrieved column info for {schema}.{table}")

            result = []
            for col in columns:
                (
                    name,
                    data_type,
                    column_default,
                    is_nullable,
                    char_max_length,
                    numeric_precision,
                    numeric_scale,
                    datetime_precision,
                    remarks,
                ) = col

                result.append(
                    {
                        "name": name,
                        "data_type": data_type,
                        "column_default": column_default,
                        "is_nullable": is_nullable,
                        "character_maximum_length": char_max_length,
                        "numeric_precision": numeric_precision,
                        "numeric_scale": numeric_scale,
                        "datetime_precision": datetime_precision,
                        "remarks": remarks,
                    }
                )

            return result

    def _get_primary_keys(self, table_name: str, schema: str) -> List[str]:
        """Get primary key columns for a given table in a schema.

        Returns:
            List of primary key column names.
        """
        logger.debug(
            f"Retrieving primary key info for table: {table_name} in schema: {schema}"
        )
        with self.connection.cursor() as cursor:
            query = (
                "SELECT k.COLUMN_NAME "
                "FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS t "
                "JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE k "
                "ON t.CONSTRAINT_NAME = k.CONSTRAINT_NAME "
                "WHERE t.TABLE_NAME = ? AND t.TABLE_SCHEMA = ? AND t.CONSTRAINT_TYPE = 'PRIMARY KEY' "
                "ORDER BY k.ORDINAL_POSITION"
            )

            cursor.execute(query, (table_name, schema))
            pk_columns = cursor.fetchall()

            logger.debug(
                f"Retrieved primary key information for table: {table_name} in schema: {schema}"
            )

            return [col[0] for col in pk_columns]

    def _get_foreign_keys(self, table_name: str, schema: str) -> List[Dict[str, str]]:
        """Get foreign key information for a given table in a schema.

        Returns:
            List of dicts with FK info:
            {
                'column_name': str,
                'referenced_schema': str,
                'referenced_table': str,
                'referenced_column': str
            }
        """
        logger.debug(f"Retrieving foreign key info for table: {schema}.{table_name}")
        with self.connection.cursor() as cursor:
            query = """
            SELECT
                k.COLUMN_NAME AS column_name,
                tc2.TABLE_SCHEMA AS referenced_schema,
                tc2.TABLE_NAME AS referenced_table,
                kcu2.COLUMN_NAME AS referenced_column
            FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
            JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE k
                ON tc.CONSTRAINT_SCHEMA = k.CONSTRAINT_SCHEMA
            AND tc.CONSTRAINT_NAME = k.CONSTRAINT_NAME
            JOIN INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS rc
                ON rc.CONSTRAINT_SCHEMA = tc.CONSTRAINT_SCHEMA
            AND rc.CONSTRAINT_NAME = tc.CONSTRAINT_NAME
            JOIN INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc2
                ON rc.UNIQUE_CONSTRAINT_SCHEMA = tc2.CONSTRAINT_SCHEMA
            AND rc.UNIQUE_CONSTRAINT_NAME = tc2.CONSTRAINT_NAME
            JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu2
                ON rc.UNIQUE_CONSTRAINT_SCHEMA = kcu2.CONSTRAINT_SCHEMA
            AND rc.UNIQUE_CONSTRAINT_NAME = kcu2.CONSTRAINT_NAME
            WHERE tc.CONSTRAINT_TYPE = 'FOREIGN KEY'
            AND tc.TABLE_SCHEMA = ?
            AND tc.TABLE_NAME = ?
            ORDER BY k.ORDINAL_POSITION
            """

            cursor.execute(query, (schema, table_name))
            fk_info = cursor.fetchall()

            logger.debug(
                f"Retrieved foreign key information for {schema}{table_name}: {fk_info}"
            )

            return [
                {
                    "column_name": fk[0],
                    "referenced_schema": fk[1],
                    "referenced_table": fk[2],
                    "referenced_column": fk[3],
                }
                for fk in fk_info
            ]

    def _get_unique_constraints(
        self, table_name: str, schema: str
    ) -> List[Dict[str, str]]:
        """Get unique constraint information for a given table in a schema.

        Returns:
            List of dicts with unique constraint info:
            {
                'constraint_name': str,
                'column_names': List[str]
            }
        """
        logger.debug(f"Retrieving unique constraint info for {schema}.{table_name}")

        with self.connection.cursor() as cursor:
            query = """
            SELECT TC.CONSTRAINT_NAME, KCU.COLUMN_NAME
            FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS AS TC
            JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE AS KCU
                ON TC.CONSTRAINT_SCHEMA = KCU.CONSTRAINT_SCHEMA
            AND TC.CONSTRAINT_NAME = KCU.CONSTRAINT_NAME
            WHERE TC.TABLE_SCHEMA = ?
            AND TC.TABLE_NAME = ?
            AND TC.CONSTRAINT_TYPE = 'UNIQUE'
            ORDER BY KCU.ORDINAL_POSITION;
            """

            cursor.execute(query, (schema, table_name))
            unique_constraints = cursor.fetchall()

            logger.debug(
                f"Retrieved unique constraint information for {schema}.{table_name}"
            )

            constraints_dict = {}
            for uc in unique_constraints:
                constraint_name = uc[0]
                column_name = uc[1]
                if constraint_name not in constraints_dict:
                    constraints_dict[constraint_name] = []
                constraints_dict[constraint_name].append(column_name)

            return [
                {"constraint_name": name, "column_names": cols}
                for name, cols in constraints_dict.items()
            ]

    def _get_check_constraints(
        self, table_name: str, schema: str
    ) -> List[Dict[str, str]]:
        """Get check constraint information for a given table in a schema.

        Returns:
            List of dicts with check constraint info:
            {
                'constraint_name': str,
                'check_clause': str
            }
        """
        logger.debug(f"Retrieving check constraint info for {schema}.{table_name}")
        with self.connection.cursor() as cursor:
            query = """
            SELECT 
                'CONSTRAINT "' || CC.CONSTRAINT_NAME || 
                '" CHECK(' || CC.CHECK_CLAUSE || ')' AS CHECK_CONSTRAINT
            FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS AS TC
            JOIN INFORMATION_SCHEMA.CHECK_CONSTRAINTS AS CC
                ON TC.CONSTRAINT_SCHEMA = CC.CONSTRAINT_SCHEMA
            AND TC.CONSTRAINT_NAME = CC.CONSTRAINT_NAME
            WHERE TC.TABLE_SCHEMA = ?
            AND TC.TABLE_NAME = ?
            AND CC.CHECK_CLAUSE IS NOT NULL;
            """

            cursor.execute(query, (schema, table_name))
            check_constraints = cursor.fetchall()

            logger.debug(
                f"Retrieved check constraint information for {schema}.{table_name}"
            )

            return [{"check_clause": cc[0]} for cc in check_constraints]

    def _get_sample_rows(
        self, table_name: str, schema: str, limit: int = 3
    ) -> List[Dict[str, Any]]:
        """Get sample rows from a given table in a schema.

        Returns:
            List of rows as dictionaries
        """
        logger.debug(
            f"Retrieving sample rows for table: {table_name} in schema: {schema}"
        )
        with self.connection.cursor() as cursor:
            query = (
                f'SELECT * FROM "{schema}"."{table_name}" FETCH FIRST {limit} ROWS ONLY'
            )
            cursor.execute(query)
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()

            return [dict(zip(columns, row)) for row in rows]
