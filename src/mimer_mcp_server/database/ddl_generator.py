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
from typing import List

from mimer_mcp_server.database.schema_inspector import SchemaInspector
from mimer_mcp_server.utils import parse_domains, format_sql_type

logger = logging.getLogger(__name__)


class DDLGenerator:
    """Class to generate DDL statements for Mimer SQL Database."""

    def __init__(self, connection):
        self.connection = connection

    def _generate_create_table_ddl(self, table_name: str, schema: str) -> str:
        """Get table schemas from a given table and schema.

        Returns:
            Formatted string with CREATE TABLE statement
        """
        logger.debug(
            f"Getting table schemas for table: {table_name} in schema: {schema}"
        )
        result = []

        with self.connection.cursor() as cursor:
            query = """
            SELECT 'CREATE TABLE "' ||
                    CASE WHEN TABLE_SCHEMA = CURRENT_USER THEN '' ELSE TABLE_SCHEMA || '"."' END ||
                    TABLE_NAME || '"(' || ascii_char(10), '' as CONSTRAINT_NAME, -1 as LINE_NUMBER
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ? AND TABLE_TYPE = 'BASE TABLE'
            
            UNION ALL
            
            SELECT CASE WHEN ORDINAL_POSITION = 1 THEN '     "' ELSE '   , "' END || COLUMN_NAME || '" ' ||
                    CASE WHEN DOMAIN_NAME IS NOT NULL THEN ' "' || DOMAIN_SCHEMA || '"."' || DOMAIN_NAME || '"' COLLATE SQL_IDENTIFIER 
                        ELSE 
                            CASE WHEN DATA_TYPE = 'USER-DEFINED' THEN
                                    CASE WHEN USER_DEFINED_TYPE_SCHEMA = CURRENT_USER THEN '' ELSE USER_DEFINED_TYPE_SCHEMA || '.' END ||
                                    USER_DEFINED_TYPE_NAME
                            ELSE DATA_TYPE COLLATE SQL_IDENTIFIER ||
                                    CASE DATA_TYPE
                                    WHEN 'DOUBLE PRECISION' THEN ''
                                    WHEN 'REAL' THEN ''
                                    WHEN 'FLOAT' THEN ''
                                    WHEN 'INTEGER' THEN ''
                                    WHEN 'SMALLINT' THEN ''
                                    WHEN 'BIGINT' THEN ''
                                    WHEN 'DATE' THEN ''
                                    WHEN 'INTERVAL' THEN CASE INTERVAL_TYPE
                                        WHEN 'YEAR TO MONTH' THEN ' YEAR(' || CAST(INTERVAL_PRECISION AS VARCHAR(1)) || ') TO MONTH'
                                        WHEN 'DAY TO HOUR' THEN ' DAY(' || CAST(INTERVAL_PRECISION AS VARCHAR(1)) || ') TO HOUR'
                                        WHEN 'DAY TO MINUTE' THEN ' DAY(' || CAST(INTERVAL_PRECISION AS VARCHAR(1)) || ') TO MINUTE'
                                        WHEN 'DAY TO SECOND' THEN ' DAY(' || CAST(INTERVAL_PRECISION AS VARCHAR(1)) || ') TO SECOND(' || CAST(DATETIME_PRECISION AS VARCHAR(1)) || ')'
                                        WHEN 'HOUR TO MINUTE' THEN ' HOUR(' || CAST(INTERVAL_PRECISION AS VARCHAR(1)) || ') TO MINUTE'
                                        WHEN 'HOUR TO SECOND' THEN ' HOUR(' || CAST(INTERVAL_PRECISION AS VARCHAR(1)) || ') TO SECOND(' || CAST(DATETIME_PRECISION AS VARCHAR(1)) || ')'
                                        WHEN 'MINUTE TO SECOND' THEN ' MINUTE(' || CAST(INTERVAL_PRECISION AS VARCHAR(2)) || ') TO SECOND(' || CAST(DATETIME_PRECISION AS VARCHAR(1)) || ')'
                                        WHEN 'SECOND' THEN ' SECOND(' || CAST(INTERVAL_PRECISION AS VARCHAR(2)) || ', ' || CAST(DATETIME_PRECISION AS VARCHAR(1)) || ')'
                                        ELSE ' ' || INTERVAL_TYPE || '(' || CAST(INTERVAL_PRECISION AS VARCHAR(2)) || ')'
                                        END
                                    WHEN 'DECIMAL' THEN '(' || CAST(NUMERIC_PRECISION AS VARCHAR(2)) || ', ' || CAST(NUMERIC_SCALE AS VARCHAR(2)) || ')'
                                    WHEN 'NUMERIC' THEN '(' || CAST(NUMERIC_PRECISION AS VARCHAR(2)) || ', ' || CAST(NUMERIC_SCALE AS VARCHAR(2)) || ')'
                                    ELSE CASE WHEN COALESCE(NUMERIC_PRECISION,CHARACTER_MAXIMUM_LENGTH,LOB_MAXIMUM_LENGTH,DATETIME_PRECISION) IS NULL THEN ''
                                        ELSE '(' || CAST(COALESCE(NUMERIC_PRECISION,CHARACTER_MAXIMUM_LENGTH,LOB_MAXIMUM_LENGTH,DATETIME_PRECISION) AS VARCHAR(20)) || ')'
                                        END
                                    END
                            END
                    END ||
                    CASE WHEN COLLATION_NAME IS NOT NULL AND (
                                (COLLATION_SCHEMA <> 'INFORMATION_SCHEMA' OR
                                (COLLATION_NAME <> 'ISO8BIT' AND COLLATION_NAME <> 'UCS_BASIC'))) THEN ' COLLATE ' || COLLATION_NAME
                        ELSE ''
                        END ||
                    CASE WHEN COLUMN_DEFAULT IS NOT NULL THEN ' DEFAULT ' || COLUMN_DEFAULT
                        ELSE ''
                        END || ascii_char(10), '' as CONSTRAINT_NAME, ORDINAL_POSITION as LINE_NUMBER
            FROM information_schema.columns
            WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
            
            UNION ALL
            
            SELECT TRIM(TRAILING FROM
                    CASE WHEN ORDINAL_POSITION = 1
                    THEN CASE WHEN TC.CONSTRAINT_TYPE = 'FOREIGN KEY' 
                        THEN '   , ' || CONSTRAINT_TYPE || '("' || COLUMN_NAME || '"'
                        ELSE '   , CONSTRAINT "' || TC.CONSTRAINT_NAME || '" ' || CONSTRAINT_TYPE || '("' || COLUMN_NAME || '"'
                        END
                    ELSE ', "' || COLUMN_NAME || '"'
                    END) ||
                    TRIM(TRAILING FROM
                    CASE WHEN ORDINAL_POSITION =
                                (SELECT MAX(ORDINAL_POSITION) FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
                                WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
                                AND CONSTRAINT_SCHEMA = TC.CONSTRAINT_SCHEMA
                                AND CONSTRAINT_NAME = TC.CONSTRAINT_NAME)
                        THEN ')' || CASE WHEN TC.CONSTRAINT_TYPE = 'FOREIGN KEY'
                                        THEN ' REFERENCES "' ||
                                            (SELECT TC2.TABLE_SCHEMA || '"."' || TC2.TABLE_NAME || '" ("' || KCU2.COLUMN_NAME || '")'
                                            FROM INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS RC 
                                            JOIN INFORMATION_SCHEMA.TABLE_CONSTRAINTS TC2
                                            ON RC.UNIQUE_CONSTRAINT_SCHEMA = TC2.CONSTRAINT_SCHEMA
                                            AND RC.UNIQUE_CONSTRAINT_NAME = TC2.CONSTRAINT_NAME
                                            JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE KCU2
                                            ON RC.UNIQUE_CONSTRAINT_SCHEMA = KCU2.CONSTRAINT_SCHEMA
                                            AND RC.UNIQUE_CONSTRAINT_NAME = KCU2.CONSTRAINT_NAME
                                            WHERE RC.CONSTRAINT_SCHEMA = TC.CONSTRAINT_SCHEMA
                                            AND RC.CONSTRAINT_NAME = TC.CONSTRAINT_NAME)
                                        ELSE '' END || ASCII_CHAR(10)
                        ELSE '' END)
            , TC.CONSTRAINT_NAME, CU.ORDINAL_POSITION
            FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS TC 
            JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE CU
            ON (TC.CONSTRAINT_SCHEMA = CU.CONSTRAINT_SCHEMA AND
                TC.CONSTRAINT_NAME = CU.CONSTRAINT_NAME)
            WHERE TC.CONSTRAINT_TYPE IN ('UNIQUE','PRIMARY KEY','FOREIGN KEY')
            AND TC.TABLE_SCHEMA = ? AND TC.TABLE_NAME = ?
            
            UNION ALL

            SELECT '   , CONSTRAINT "' || CC.CONSTRAINT_NAME || '" CHECK(' || CC.CHECK_CLAUSE || ')' || ascii_char(10), CC.CONSTRAINT_NAME, 1
            FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS DC
            JOIN INFORMATION_SCHEMA.CHECK_CONSTRAINTS CC
            ON (DC.CONSTRAINT_SCHEMA = CC.CONSTRAINT_SCHEMA AND
                DC.CONSTRAINT_NAME = CC.CONSTRAINT_NAME)
            WHERE DC.TABLE_SCHEMA = ? AND DC.TABLE_NAME = ?
            AND CC.CHECK_CLAUSE IS NOT NULL
            
            UNION ALL
            
            SELECT CASE WHEN SD.LINE_NUMBER = 1
                        THEN '   , CONSTRAINT "' || CC.CONSTRAINT_NAME ||
                                '"' || ascii_char(10) ||'          CHECK('
                        ELSE ''
                        END ||
                    SD.SOURCE_DEFINITION ||
                    CASE WHEN SD.LINE_NUMBER = (SELECT MAX(LINE_NUMBER) FROM INFORMATION_SCHEMA.EXT_SOURCE_DEFINITION SD2
                                                WHERE SD2.OBJECT_SCHEMA = SD.OBJECT_SCHEMA
                                                AND SD2.OBJECT_NAME = SD.OBJECT_NAME)
                        THEN ')' || ascii_char(10)
                        ELSE ''
                        END, CC.CONSTRAINT_NAME, LINE_NUMBER
            FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS TC3
            JOIN INFORMATION_SCHEMA.CHECK_CONSTRAINTS CC
            ON (TC3.CONSTRAINT_SCHEMA = CC.CONSTRAINT_SCHEMA AND
                TC3.CONSTRAINT_NAME = CC.CONSTRAINT_NAME)
            JOIN INFORMATION_SCHEMA.EXT_SOURCE_DEFINITION SD
            ON (CC.CONSTRAINT_SCHEMA = SD.OBJECT_SCHEMA AND
                CC.CONSTRAINT_NAME = SD.OBJECT_NAME)
            WHERE TC3.TABLE_SCHEMA = ? AND TC3.TABLE_NAME = ?
            AND CC.CHECK_CLAUSE IS NULL
            
            UNION ALL
            
            SELECT ')', ascii_char(255), 10000
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ? AND TABLE_TYPE = 'BASE TABLE'
            ORDER BY CONSTRAINT_NAME, LINE_NUMBER
            """

            # Execute query with proper parameters for each table
            cursor.execute(
                query,
                (
                    schema,
                    table_name,
                    schema,
                    table_name,
                    schema,
                    table_name,
                    schema,
                    table_name,
                    schema,
                    table_name,
                    schema,
                    table_name,
                    schema,
                    table_name,
                ),
            )

            rows = cursor.fetchall()

            if rows:
                # Join all the CREATE TABLE statement parts
                create_statement = "".join([row[0] for row in rows])
                result.append(create_statement)

        logger.debug(
            f"Retrieved table schemas for tables: {table_name} in schema: {schema}"
        )
        return "\n\n".join(result)

    def _generate_domain_ddl(self, domain_name: str, schema: str) -> str:
        """Get domain info for a given domain in a schema."""

        logger.debug(
            f"Retrieving domain info for domain: {domain_name} in schema: {schema}"
        )
        with self.connection.cursor() as cursor:
            query = """
                select 'CREATE DOMAIN "' ||
                case when DOMAIN_SCHEMA = CURRENT_USER then '' else DOMAIN_SCHEMA || '"."' end ||
                D.DOMAIN_NAME || '" AS ' || DATA_TYPE ||
                case DATA_TYPE
                when 'DOUBLE PRECISION' then ''
                when 'REAL' then ''
                when 'FLOAT' then ''
                when 'INTEGER' then ''
                when 'SMALLINT' then ''
                when 'BIGINT' then ''
                when 'DATE' then ''
                when 'INTERVAL'
                then case INTERVAL_TYPE
                    when 'YEAR TO MONTH'  then ' YEAR(' || cast(INTERVAL_PRECISION as varchar(1)) || ') TO MONTH'
                    when 'DAY TO HOUR'    then ' DAY('  || cast(INTERVAL_PRECISION as varchar(1)) || ') TO HOUR'
                    when 'DAY TO MINUTE'  then ' DAY('  || cast(INTERVAL_PRECISION as varchar(1)) || ') TO MINUTE'
                    when 'DAY TO SECOND'  then ' DAY('  || cast(INTERVAL_PRECISION as varchar(1)) || ') TO SECOND(' || cast(DATETIME_PRECISION as varchar(1)) || ')'
                    when 'HOUR TO MINUTE' then ' HOUR('  || cast(INTERVAL_PRECISION as varchar(1)) || ') TO MINUTE'
                    when 'HOUR TO SECOND' then ' HOUR('  || cast(INTERVAL_PRECISION as varchar(1)) || ') TO SECOND(' || cast(DATETIME_PRECISION as varchar(1)) || ')'
                    when 'MINUTE TO SECOND' then ' MINUTE('  || cast(INTERVAL_PRECISION as varchar(2)) || ') TO SECOND(' || cast(DATETIME_PRECISION as varchar(1)) || ')'
                    when 'SECOND' then ' SECOND('  || cast(INTERVAL_PRECISION as varchar(2)) || ', ' || cast(DATETIME_PRECISION as varchar(1)) || ')'
                    else ' ' || INTERVAL_TYPE || '(' || cast(INTERVAL_PRECISION as varchar(2)) || ')'
                    end
                when 'DECIMAL' then '('  || cast(NUMERIC_PRECISION as varchar(2)) || ', ' || cast(NUMERIC_SCALE as varchar(2)) || ')'
                when 'NUMERIC' then '('  || cast(NUMERIC_PRECISION as varchar(2)) || ', ' || cast(NUMERIC_SCALE as varchar(2)) || ')'
                else case when coalesce(NUMERIC_PRECISION,CHARACTER_MAXIMUM_LENGTH,LOB_MAXIMUM_LENGTH,DATETIME_PRECISION) is NULL then ''
                    else '(' || cast(coalesce(NUMERIC_PRECISION,CHARACTER_MAXIMUM_LENGTH,LOB_MAXIMUM_LENGTH,DATETIME_PRECISION) as varchar(20)) || ')'
                    end
                end ||
                case when COLLATION_NAME is not null and (
                        (COLLATION_SCHEMA <> 'INFORMATION_SCHEMA' or
                        (COLLATION_NAME <> 'ISO8BIT' and COLLATION_NAME <> 'UCS_BASIC'))) then ' COLLATE ' || COLLATION_NAME
                    else ''
                    end ||
                case when DOMAIN_DEFAULT is not null and DOMAIN_DEFAULT <> 'TRUNCATED' then ascii_char(10) || '     DEFAULT ' || DOMAIN_DEFAULT
                    else ''
                    end,
                '' as CONSTRAINT_NAME,
                0  as LINE_NUMBER
                from INFORMATION_SCHEMA.DOMAINS D
                where D.DOMAIN_SCHEMA = ?
                and D.DOMAIN_NAME = ?
                union all
                select case when SD3.LINE_NUMBER = 1
                            then ascii_char(10) || '     default '
                            else ''
                            end ||
                            SD3.SOURCE_DEFINITION collate SQL_IDENTIFIER
                    ,'',
                    SD3.LINE_NUMBER
                from INFORMATION_SCHEMA.EXT_SOURCE_DEFINITION SD3
                where OBJECT_SCHEMA = ?
                and   OBJECT_NAME = ?
                and   OBJECT_TYPE = 'DOMAIN'
                union all
                select ascii_char(10) || '     CONSTRAINT "' || CC.CONSTRAINT_NAME || '" CHECK(' || CC.CHECK_CLAUSE || ')', CC.CONSTRAINT_NAME, 1
                from INFORMATION_SCHEMA.DOMAIN_CONSTRAINTS DC
                join INFORMATION_SCHEMA.CHECK_CONSTRAINTS CC
                on (DC.CONSTRAINT_SCHEMA = CC.CONSTRAINT_SCHEMA and
                    DC.CONSTRAINT_NAME = CC.CONSTRAINT_NAME)
                where DC.DOMAIN_SCHEMA = ?
                and DC.DOMAIN_NAME = ?
                and CC.CHECK_CLAUSE is not null
                union all
                select case when SD.LINE_NUMBER = 1
                            then ascii_char(10) || '     CONSTRAINT "' || CC.CONSTRAINT_NAME || '" CHECK('
                            else ''
                            end ||
                    SD.SOURCE_DEFINITION ||
                    case when SD.LINE_NUMBER = (select max(LINE_NUMBER) from INFORMATION_SCHEMA.EXT_SOURCE_DEFINITION SD2
                                                where SD2.OBJECT_SCHEMA = SD.OBJECT_SCHEMA
                                                and SD2.OBJECT_NAME = SD.OBJECT_NAME)
                            then ')'
                            else ''
                            end, CC.CONSTRAINT_NAME, LINE_NUMBER
                from INFORMATION_SCHEMA.DOMAIN_CONSTRAINTS DC
                join INFORMATION_SCHEMA.CHECK_CONSTRAINTS CC
                on (DC.CONSTRAINT_SCHEMA = CC.CONSTRAINT_SCHEMA and
                    DC.CONSTRAINT_NAME = CC.CONSTRAINT_NAME)
                join INFORMATION_SCHEMA.EXT_SOURCE_DEFINITION SD
                on (CC.CONSTRAINT_SCHEMA = SD.OBJECT_SCHEMA and
                    CC.CONSTRAINT_NAME = SD.OBJECT_NAME)
                where DC.DOMAIN_SCHEMA = ?
                and DC.DOMAIN_NAME = ?
                and CC.CHECK_CLAUSE is null
                order by CONSTRAINT_NAME, LINE_NUMBER
            """

            cursor.execute(
                query,
                (
                    schema,
                    domain_name,  # DOMAINS
                    schema,
                    domain_name,  # EXT_SOURCE_DEFINITION SD3
                    schema,
                    domain_name,  # DOMAIN_CONSTRAINTS with CHECK_CLAUSE not null
                    schema,
                    domain_name,  # DOMAIN_CONSTRAINTS with CHECK_CLAUSE null
                ),
            )
            rows = cursor.fetchall()
            logger.debug(
                f"Retrieved domain information for domain: {domain_name} in schema: {schema}"
            )
            return "".join([row[0] for row in rows]) if rows else ""

    # OBSOLETE: Detailed version of format_table_info that includes domain info
    def _format_table_info_with_samples(
        self,
        table_names: List[str],
        schema: str,
        sample_size: int = 3,
        domain_info: bool = True,  # Whether to include domain info
    ) -> str:
        """Get table schemas (dbvi) and sample rows.

        Returns:
            Formatted string with CREATE TABLE statement and sample rows.
        """
        logger.debug(
            f"Getting table info for tables: {table_names} in schema: {schema}"
        )
        result = []

        for table_name in table_names:
            # column_info = []
            column_names = []

            # Get column information
            # columns = self._get_columns(table_name, schema)
            # for col in columns:
            #     column_names.append(col["name"])
            #     formatted_data_type = self._format_data_type(col)
            #     column_info.append(
            #         f'    "{col["name"]}" {formatted_data_type} {col["is_nullable"]}'
            #     )

            table_info = []
            # Get table DDL
            table_ddl = self._generate_create_table_ddl(table_name, schema).splitlines()

            # Get domain info
            if domain_info:
                domain_names = parse_domains("\n".join(table_ddl))
                for domain_schema, domain_name in domain_names:
                    domain_ddl = self._generate_domain_ddl(domain_name, domain_schema)
                    if domain_ddl:
                        table_info.append(domain_ddl)
                        logger.debug(
                            f"Added domain info for domain: {domain_name} in schema: {domain_schema}"
                        )
                    else:
                        logger.info(
                            f"No domain info found for domain: {domain_name} in schema: {domain_schema}"
                        )
                        table_info.append(
                            f"/* No domain info found for domain: {domain_name} in schema: {domain_schema} */"
                        )

            table_info.extend(table_ddl)

            # Get sample rows
            sample_rows = self.connection._get_sample_rows(
                table_name, schema, limit=sample_size
            )

            # Add sample rows as comment
            if sample_rows:
                comment_lines = [
                    f"/*\n{len(sample_rows)} rows from {table_name} table:"
                ]
                comment_lines.append(" ".join(column_names))

                for row in sample_rows:
                    row_values = [
                        str(row[col]) if row[col] is not None else "NULL"
                        for col in column_names
                    ]
                    comment_lines.append(" ".join(row_values))

                comment_lines.append("*/")
                table_info.append("\n".join(comment_lines))
            else:
                logger.info(f"No sample rows found for table: {table_name}")
                table_info.append(f"/* No rows in {table_name} table */")

            result.append("\n".join(table_info))

        logger.debug("Formatted table info and sample rows")
        return "\n\n".join(result)

    # TODO: COLLATE e.g. "country" "mimer_store"."name" COLLATE ENGLISH_1
    # TODO: domain constraints are not included,
    #       e.g. DOMAIN "euros" CONSTRAINT "euros_value_illegal" CHECK(value > 0.0)
    def format_table_info_with_samples(
        self, table_names: List[str], schema: str, sample_size: int = 3
    ) -> str:
        """Get table schemas and sample rows.

        Returns:
            Formatted string with CREATE TABLE statement and sample rows.
        """
        logger.debug(
            f"Getting table info for tables: {table_names} in schema: {schema}"
        )
        result = []

        for table_name in table_names:
            column_info = []
            column_names = []
            constraint_info = []

            # Get column information
            inspector = SchemaInspector(self.connection)
            columns = inspector._get_columns(table_name, schema)
            for col in columns:
                column_names.append(col["name"])
                formatted_data_type = format_sql_type(col)

                # Include DEFAULT only if it is not None, otherwise skip it
                default_value = (
                    f" DEFAULT {col['column_default']}"
                    if col["column_default"] is not None
                    else ""
                )

                is_nullable = " NOT NULL" if col["is_nullable"] == "NO" else ""

                comment = (
                    f" COMMENT '{col['remarks']}'" if col["remarks"] is not None else ""
                )

                column_info.append(
                    f'    "{col["name"]}" {formatted_data_type}{default_value}{is_nullable}{comment}'
                )

            # Get primary keys
            pk_columns = inspector._get_primary_keys(table_name, schema)
            if pk_columns:
                pk_cols = ", ".join([f'"{col}"' for col in pk_columns])
                constraint_info.append(f"    PRIMARY KEY ({pk_cols})")

            # Get foreign keys
            fk_columns = inspector._get_foreign_keys(table_name, schema)
            for fk in fk_columns:
                constraint_info.append(
                    f'    FOREIGN KEY("{fk["column_name"]}") REFERENCES "{fk["referenced_schema"]}"."{fk["referenced_table"]}" ("{fk["referenced_column"]}")'
                )

            # Get unique constraints
            unique_constraints = inspector._get_unique_constraints(table_name, schema)
            for uc in unique_constraints:
                uc_cols = ", ".join([f'"{col}"' for col in uc["column_names"]])
                constraint_info.append(
                    f'    CONSTRAINT "{uc["constraint_name"]}" UNIQUE ({uc_cols})'
                )

            # Get CHECK constraints
            check_constraints = inspector._get_check_constraints(table_name, schema)
            if check_constraints:
                # check if check_constraints does not contain "is not null"
                # which is already covered by NOT NULL in _get_columns
                for cc in check_constraints:
                    if "is not null" not in cc["check_clause"].lower():
                        constraint_info.append(f"    {cc['check_clause']}")

            # Get sample rows
            sample_rows = inspector._get_sample_rows(
                table_name, schema, limit=sample_size
            )

            # Format CREATE TABLE statement
            table_info = [f'CREATE TABLE "{table_name}" (']
            table_info.extend([f"{col}," for col in column_info])

            if constraint_info:
                # Add constraints (last one without comma)
                for i, constraint in enumerate(constraint_info):
                    if i == len(constraint_info) - 1:
                        table_info.append(constraint)
                    else:
                        table_info.append(f"{constraint},")
            else:
                # Remove trailing comma from last column
                table_info[-1] = table_info[-1].rstrip(",")

            table_info.append(")")

            # Add sample rows as comment
            if sample_rows:
                comment_lines = [
                    f"/*\n{len(sample_rows)} rows from {table_name} table:"
                ]
                comment_lines.append(" ".join(column_names))

                for row in sample_rows:
                    row_values = [
                        str(row[col]) if row[col] is not None else "NULL"
                        for col in column_names
                    ]
                    comment_lines.append(" ".join(row_values))

                comment_lines.append("*/")
                table_info.append("\n".join(comment_lines))
            else:
                table_info.append(f"/* No rows in {table_name} table */")

            result.append("\n".join(table_info))

        logger.debug("Formatted table info and sample rows")
        return "\n\n".join(result)
