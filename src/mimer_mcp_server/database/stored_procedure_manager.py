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
import json
import decimal
import datetime
import re

from mimer_mcp_server.database.schema_inspector import SchemaInspector
from mimer_mcp_server.utils import format_sql_type


logger = logging.getLogger(__name__)


class StoredProcedureManager:
    """Manager for stored procedures in Mimer SQL Database.

    This class provides methods to list stored procedures, their definitions and parameters, and execute them
    within the connected Mimer SQL database.
    """

    def __init__(self, connection):
        self.connection = connection
        self._schema_inspector = SchemaInspector(connection)

    def _schema_exists(self, schema: str) -> bool:
        """Check if a schema exists."""
        return self._schema_inspector.schema_exists(schema)

    def _stored_procedure_name_exists(self, procedure_name: str) -> bool:
        """Check if a procedure name exists in any schema."""
        logger.debug(
            f"Checking existence of stored procedure name across schemas: {procedure_name}"
        )
        with self.connection.cursor() as cursor:
            query = """
                SELECT CASE WHEN EXISTS (
                    SELECT 1
                    FROM INFORMATION_SCHEMA.ROUTINES
                    WHERE ROUTINE_NAME = ?
                      AND ROUTINE_TYPE = 'PROCEDURE'
                ) THEN 1 ELSE 0 END
                FROM SYSTEM.ONEROW
            """
            cursor.execute(query, (procedure_name,))
            row = cursor.fetchone()
            return bool(row and row[0] == 1)

    def _stored_procedure_exists(
        self, procedure_schema: str, procedure_name: str
    ) -> bool:
        """Check if a stored procedure exists in a given schema."""
        logger.debug(
            f"Checking existence of stored procedure {procedure_schema}.{procedure_name}"
        )

        with self.connection.cursor() as cursor:
            query = """
                SELECT CASE WHEN EXISTS (
                    SELECT 1
                    FROM INFORMATION_SCHEMA.ROUTINES
                    WHERE ROUTINE_SCHEMA = ?
                      AND ROUTINE_NAME   = ?
                      AND ROUTINE_TYPE   = 'PROCEDURE'
                ) THEN 1 ELSE 0 END
                FROM SYSTEM.ONEROW
            """

            cursor.execute(query, (procedure_schema, procedure_name))
            row = cursor.fetchone()
            return bool(row and row[0] == 1)

    def _validate_procedure_exists(
        self, procedure_schema: str, procedure_name: str
    ) -> None:
        """Validate that schema and procedure exist, raising ValueError if not.

        Args:
            procedure_schema: The schema to validate
            procedure_name: The procedure name to validate

        Raises:
            ValueError: If schema or procedure doesn't exist with descriptive message
        """
        if not self._schema_exists(procedure_schema):
            message = f"Schema '{procedure_schema}' does not exist."
            logger.error(message)
            raise ValueError(message)

        if not self._stored_procedure_name_exists(procedure_name):
            message = f"Stored procedure name '{procedure_name}' does not exist in any schema."
            logger.error(message)
            raise ValueError(message)

        if not self._stored_procedure_exists(procedure_schema, procedure_name):
            message = f"Stored procedure '{procedure_name}' does not exist in schema '{procedure_schema}'."
            logger.error(message)
            raise ValueError(message)

    def list_stored_procedures(self) -> list[Dict[str, Any]]:
        """List stored procedures in the connected database.

        Returns:
            List of dicts with stored procedure info: {procedure_schema, procedure_name, remark}
        """
        logger.debug("Listing stored procedures in the database")

        with self.connection.cursor() as cursor:
            # TODO: allow procedures with different SQL_DATA_ACCESS types, e.g. 'CONTAINS SQL', 'MODIFIES SQL'
            # TODO: review if SPECIFIC_SCHEMA and SPECIFIC_NAME should be used instead of ROUTINE_SCHEMA and ROUTINE_NAME
            query = """
                SELECT ROUTINE_SCHEMA, ROUTINE_NAME
                FROM INFORMATION_SCHEMA.ROUTINES
                WHERE ROUTINE_TYPE = 'PROCEDURE' AND
                        SQL_DATA_ACCESS = 'READS SQL DATA'
                ORDER BY ROUTINE_SCHEMA, ROUTINE_NAME
            """

            cursor.execute(query)
            procedures = cursor.fetchall()

            logger.debug("Retrieved stored procedure information")

            result = []
            for proc in procedures:
                procedure_schema, procedure_name = proc
                remark = None

                query = """
                    SELECT REMARKS
                    FROM INFORMATION_SCHEMA.EXT_OBJECT_IDENT_USAGE
                    WHERE OBJECT_SCHEMA = ?
                    AND OBJECT_NAME = ?
                    AND OBJECT_TYPE = 'PROCEDURE'"""

                cursor.execute(query, (procedure_schema, procedure_name))
                remark_row = cursor.fetchone()
                if remark_row and remark_row[0] is not None:
                    remark = remark_row[0]
                    logger.debug(
                        f"Retrieved remark from EXT_OBJECT_IDENT_USAGE for {procedure_schema}.{procedure_name}: {remark}"
                    )
                else:
                    # Fallback: extract from procedure definition
                    procedure_definition = self.get_stored_procedure_definition(
                        procedure_schema, procedure_name
                    )
                    remark = self._extract_stored_procedure_comment(
                        procedure_definition
                    )
                    if remark:
                        logger.debug(
                            f"Extracted remark from definition for {procedure_schema}.{procedure_name}: {remark}"
                        )
                    else:
                        logger.info(
                            f"No remark found for {procedure_schema}.{procedure_name}"
                        )

                result.append(
                    {
                        "procedure_schema": procedure_schema,
                        "procedure_name": procedure_name,
                        "remark": remark,
                    }
                )

            return result

    def get_stored_procedure_definition(
        self, procedure_schema: str, procedure_name: str
    ) -> str:
        """Get stored procedure definition for a given procedure in a schema.

        Returns:
            String containing the complete stored procedure definition, or raises ValueError if not found.
        """
        logger.debug(
            f"Getting stored procedure definition for {procedure_schema}.{procedure_name}"
        )
        self._validate_procedure_exists(procedure_schema, procedure_name)

        with self.connection.cursor() as cursor:
            # 1) Try to read inline definition from INFORMATION_SCHEMA.ROUTINES
            routines_query = """
                    SELECT ROUTINE_DEFINITION
                    FROM INFORMATION_SCHEMA.ROUTINES
                    WHERE ROUTINE_SCHEMA = ?
                    AND ROUTINE_NAME = ?
                    AND ROUTINE_TYPE = 'PROCEDURE'
                """

            cursor.execute(routines_query, (procedure_schema, procedure_name))
            routine_row = cursor.fetchone()

            if routine_row and routine_row[0] is not None:
                logger.debug(
                    f"Retrieved stored procedure definition from ROUTINES for {procedure_schema}.{procedure_name}"
                )
                return routine_row[0]

            # 2) Fallback to extended source view when definition does not fit
            ext_query = """
                    SELECT SOURCE_DEFINITION
                    FROM INFORMATION_SCHEMA.EXT_SOURCE_DEFINITION
                    WHERE OBJECT_SCHEMA = ? 
                    AND OBJECT_NAME = ? 
                    AND OBJECT_TYPE = 'PROCEDURE'
                    ORDER BY LINE_NUMBER
                """

            cursor.execute(ext_query, (procedure_schema, procedure_name))
            ext_rows = cursor.fetchall()

            if ext_rows:
                procedure_definition = "".join([row[0] for row in ext_rows])
                logger.debug(
                    f"Retrieved stored procedure definition from EXT_SOURCE_DEFINITION for {procedure_schema}.{procedure_name}"
                )
                return procedure_definition

    def _extract_stored_procedure_comment(self, procedure_definition: str):
        """Extract a descriptive comment from a stored procedure definition.

        Heuristics:
        - Prefer a line comment starting with "--" that appears after the
          CREATE PROCEDURE signature and before the first AS/BEGIN keyword.
        - If a block comment /* ... */ appears in the same region, return its
          content (first line trimmed).
        - Returns None if nothing is found.
        """
        if not procedure_definition:
            return None

        lines = procedure_definition.splitlines()

        block_comment_active = False
        block_comment_content = []

        # Normalize a function to detect header end (AS/BEGIN/RETURNS).
        def is_header_end(s: str) -> bool:
            ls = s.strip().lower()
            # Typical header terminators
            return (
                ls.startswith("as")
                or ls.startswith("begin")
                or ls.startswith("returns")
            )

        # First, find the start of the header (line containing CREATE and PROCEDURE)
        for idx, raw in enumerate(lines):
            s = raw.strip().lower()
            if "create" in s and "procedure" in s:
                # Header starts here; search subsequent lines for comments until header end
                # Search remaining lines including possibly the same line tail
                # Continue loop from next iteration
                start_idx = idx
                break
        else:
            # If we didn't find CREATE PROCEDURE, scan from top conservatively
            start_idx = 0

        for raw in lines[start_idx:]:
            line = raw.strip()
            if not line:
                # Skip empties inside header
                continue

            # Stop if header terminator reached
            if is_header_end(line):
                break

            # Handle block comments
            if block_comment_active:
                if "*/" in line:
                    # Close block and return first meaningful content
                    # Append up to before */
                    before, _sep, _after = line.partition("*/")
                    if before.strip():
                        block_comment_content.append(before.strip())
                    content = " ".join(block_comment_content).strip()
                    return content or None
                else:
                    if line.strip():
                        block_comment_content.append(line.strip())
                continue

            # Detect start of block comment
            if "/*" in line:
                block_comment_active = True
                # Capture content after /* on the same line
                _before, _sep, after = line.partition("/*")
                after = after.strip()
                # If it also closes on same line
                if "*/" in after:
                    mid, _sep2, _tail = after.partition("*/")
                    mid = mid.strip()
                    if mid:
                        return mid
                    # else keep searching
                    block_comment_active = False
                    block_comment_content = []
                else:
                    if after:
                        block_comment_content.append(after)
                continue

            # Detect single-line comment
            if line.startswith("--"):
                # Return text after the dashes
                comment_text = line[2:].strip()
                return comment_text or None

        # If a block comment was started but not properly closed before header end,
        # return what we captured.
        if block_comment_active and block_comment_content:
            return " ".join(block_comment_content).strip() or None

        return None

    def get_stored_procedure_parameters(
        self, procedure_schema: str, procedure_name: str
    ) -> List[Dict[str, Any]]:
        """Return parameters for a stored procedure.

        Returns:
            A list of schema name, procedure name, and parameter descriptors in ordinal order. Each item is a
            dict with keys:

            procedure_schema: str
            procedure_name: str
            parameters: List of parameter dicts with keys:
                - 'parameter_name': str
                - 'data_type': str (formatted, e.g. "CHARACTER VARYING(48)")
                - 'direction': str (e.g. IN, OUT, INOUT)
                - 'default_value': str or None
        """
        logger.debug(
            f"Getting stored procedure parameters for {procedure_schema}.{procedure_name}"
        )

        self._validate_procedure_exists(procedure_schema, procedure_name)

        with self.connection.cursor() as cursor:
            # TODO: Add INTERVAL_TYPE, INTERVAL_PRECISION to support INTERVAL data type
            query = """
                SELECT p.PARAMETER_NAME, p.DATA_TYPE, p.PARAMETER_DEFAULT, p.CHARACTER_MAXIMUM_LENGTH, p.NUMERIC_PRECISION, p.NUMERIC_SCALE, p.DATETIME_PRECISION, p.PARAMETER_MODE
                FROM INFORMATION_SCHEMA.ROUTINES r
                JOIN INFORMATION_SCHEMA.PARAMETERS p
                  ON p.SPECIFIC_SCHEMA = r.SPECIFIC_SCHEMA
                 AND p.SPECIFIC_NAME  = r.SPECIFIC_NAME
                WHERE r.ROUTINE_SCHEMA = ?
                  AND r.ROUTINE_NAME   = ?
                  AND r.ROUTINE_TYPE   = 'PROCEDURE'
                ORDER BY p.ORDINAL_POSITION
            """

            cursor.execute(query, (procedure_schema, procedure_name))
            parameter_rows = cursor.fetchall()

            logger.debug(
                f"Retrieved stored procedure parameters for {procedure_schema}.{procedure_name}"
            )

            params = []
            for row in parameter_rows:
                (
                    parameter_name,
                    data_type,
                    parameter_default,
                    character_maximum_length,
                    numeric_precision,
                    numeric_scale,
                    datetime_precision,
                    parameter_mode,
                ) = row

                type_info = {
                    "name": parameter_name,
                    "data_type": data_type,
                    "character_maximum_length": character_maximum_length,
                    "numeric_precision": numeric_precision,
                    "numeric_scale": numeric_scale,
                    "datetime_precision": datetime_precision,
                }
                formatted_data_type = format_sql_type(type_info)

                params.append(
                    {
                        parameter_name: {
                            "data_type": formatted_data_type,
                            "direction": parameter_mode,
                            "default_value": parameter_default,
                        }
                    }
                )

            result = {
                "procedure_schema": procedure_schema,
                "procedure_name": procedure_name,
                "parameters": params,
            }

            return result

    def execute_stored_procedure(
        self,
        procedure_schema: str,
        procedure_name: str,
        parameters: str,
    ) -> Dict[str, Any]:
        """Execute a stored procedure with automatic parameter conversion.

        Args:
            procedure_schema: The schema of the stored procedure.
            procedure_name: The name of the stored procedure.
            parameters: JSON string mapping parameter names to values.

        Returns:
            Dict with keys: 
                message: "Executed {procedure_schema}.{procedure_name} successfully.", 
                result: Dict[str, Any]

        Behavior:
            - Uses procedure metadata to convert JSON values into SQL types
            - Case-insensitive parameter name matching
            - Validates required, unknown, and order constraints with clear messages
        """
        logger.debug(
            "Preparing to execute stored procedure %s.%s with parameters: %s",
            procedure_schema,
            procedure_name,
            parameters,
        )

        self._validate_procedure_exists(procedure_schema, procedure_name)

        # Parse JSON string parameters into dict
        if not parameters:
            message = "Parameters JSON string is required."
            logger.error(message)
            raise ValueError(message)

        try:
            provided_params: Dict[str, Any] = json.loads(parameters)
            if not isinstance(provided_params, dict):
                raise ValueError(
                    "Parameters JSON must represent an object of name->value pairs."
                )
        except Exception as e:
            message = f"Invalid JSON for parameters: {e}"
            logger.error(message)
            raise ValueError(message)

        # Fetch stored procedure metadata
        meta = self.get_stored_procedure_parameters(procedure_schema, procedure_name)
        # meta['parameters'] is a list preserving ordinal order like [{name: {...}}, ...]
        ordered_params_meta: List[Dict[str, Any]] = meta.get("parameters", [])

        # Build lookup dictionaries for case-insensitive parameter matching
        lower_to_actual: Dict[str, str] = {}
        param_defs_by_lower: Dict[str, Dict[str, Any]] = {}

        expected_names_in_order: List[str] = []
        for param_desc in ordered_params_meta:
            # param_desc is { parameter_name: { data_type, direction, default_value } }
            if not isinstance(param_desc, dict) or len(param_desc) != 1:
                # Defensive: unexpected shape
                continue
            name = next(iter(param_desc.keys()))
            lower_to_actual[name.lower()] = name
            param_defs_by_lower[name.lower()] = param_desc[name]
            expected_names_in_order.append(name)

        # Validate unknown provided parameters
        unknowns = [
            k for k in provided_params.keys() if k.lower() not in lower_to_actual
        ]
        if unknowns:
            expected_csv = ", ".join(expected_names_in_order)
            message = (
                "Unknown parameter(s): "
                + ", ".join(unknowns)
                + f". Expected one of: {expected_csv} (case-insensitive)."
            )
            logger.error(message)
            raise ValueError(message)

        # Helper: parse base type from formatted type string, e.g., "DECIMAL(10,2)" -> "DECIMAL"
        def _base_type(type_str: str) -> str:
            if not type_str:
                return ""
            return re.split(r"\s*\(", type_str.strip(), maxsplit=1)[0].upper()

        # Conversion based on base data type
        def _convert_value(value: Any, type_str: str, param_name: str) -> Any:
            base = _base_type(type_str)
            # Strings
            if base in {
                "CHARACTER",
                "CHARACTER VARYING",
                "NATIONAL CHARACTER",
                "NATIONAL CHARACTER VARYING",
                "CLOB",
                "NCLOB",
            }:
                if value is None:
                    return None
                if isinstance(value, (str, int, float, bool)):
                    return str(value)
                message = f"Parameter '{param_name}' expects TEXT but got {type(value).__name__}."
                raise ValueError(message)

            # Integers
            if base in {"INTEGER", "SMALLINT", "BIGINT"}:
                if value is None:
                    return None
                try:
                    return int(value)
                except Exception:
                    message = (
                        f"Parameter '{param_name}' expects INTEGER but got '{value}'."
                    )
                    raise ValueError(message)

            # Floating point
            if base in {"REAL", "FLOAT", "DOUBLE PRECISION"}:
                if value is None:
                    return None
                try:
                    return float(value)
                except Exception:
                    message = (
                        f"Parameter '{param_name}' expects FLOAT but got '{value}'."
                    )
                    raise ValueError(message)

            # Decimal / Numeric
            if base in {"DECIMAL", "NUMERIC"}:
                if value is None:
                    return None
                try:
                    return decimal.Decimal(str(value))
                except Exception:
                    message = (
                        f"Parameter '{param_name}' expects DECIMAL but got '{value}'."
                    )
                    raise ValueError(message)

            # Boolean
            if base in {"BOOLEAN"}:
                if value is None:
                    return None
                if isinstance(value, bool):
                    return value
                if isinstance(value, str):
                    lv = value.strip().lower()
                    if lv in {"true", "t", "1", "yes", "y"}:
                        return True
                    if lv in {"false", "f", "0", "no", "n"}:
                        return False
                if isinstance(value, (int, float)):
                    return bool(value)
                message = f"Parameter '{param_name}' expects BOOLEAN but got '{value}'."
                raise ValueError(message)

            # Date/Time
            if base == "DATE":
                if value is None:
                    return None
                try:
                    return datetime.date.fromisoformat(str(value))
                except Exception:
                    message = f"Parameter '{param_name}' expects DATE (YYYY-MM-DD) but got '{value}'."
                    raise ValueError(message)

            if base == "TIME":
                if value is None:
                    return None
                try:
                    # fromisoformat allows HH:MM[:SS[.ffffff]]
                    return datetime.time.fromisoformat(str(value))
                except Exception:
                    message = f"Parameter '{param_name}' expects TIME (HH:MM[:SS[.fff]]) but got '{value}'."
                    raise ValueError(message)

            if base == "TIMESTAMP":
                if value is None:
                    return None
                try:
                    # fromisoformat supports 'YYYY-MM-DD HH:MM:SS[.ffffff]' and 'YYYY-MM-DDTHH:MM:SS[.ffffff]'
                    s = str(value).replace("T", " ")
                    return datetime.datetime.fromisoformat(s)
                except Exception:
                    message = f"Parameter '{param_name}' expects TIMESTAMP (ISO 8601) but got '{value}'."
                    raise ValueError(message)

            # Binary
            if base in {"BINARY", "VARBINARY", "BLOB"}:
                if value is None:
                    return None
                if isinstance(value, (bytes, bytearray)):
                    return bytes(value)
                if isinstance(value, str):
                    # Accept hex strings like 0xABCD or ABCD
                    hex_str = value.strip().lower()
                    if hex_str.startswith("0x"):
                        hex_str = hex_str[2:]
                    try:
                        return bytes.fromhex(hex_str)
                    except Exception:
                        pass
                message = f"Parameter '{param_name}' expects BINARY (bytes or hex string) but got '{value}'."
                raise ValueError(message)

            # Fallback: pass through
            return value

        # Build ordered argument list for IN/INOUT parameters
        ordered_argument_values: List[Any] = []
        provided_lower_to_value: Dict[str, Any] = {
            k.lower(): v for k, v in provided_params.items()
        }

        # Track last provided index to enforce trailing-default omission rule
        last_provided_index = -1
        for idx, exp_name in enumerate(expected_names_in_order):
            lower = exp_name.lower()
            definition = param_defs_by_lower[lower]
            direction = (definition.get("direction") or "IN").upper()
            if direction not in {"IN", "INOUT", "OUT"}:
                direction = "IN"

            if direction == "OUT":
                # OUT-only parameters are not passed as arguments in CALL
                continue

            if lower in provided_lower_to_value:
                last_provided_index = idx

        # Validate missing required parameters up to last provided index
        errors: List[str] = []
        for idx, exp_name in enumerate(expected_names_in_order):
            lower = exp_name.lower()
            definition = param_defs_by_lower[lower]
            direction = (definition.get("direction") or "IN").upper()
            if direction == "OUT":
                continue

            has_value = lower in provided_lower_to_value
            has_default = definition.get("default_value") is not None
            if idx <= last_provided_index and not has_value and not has_default:
                errors.append(
                    f"Missing required parameter '{exp_name}' before later parameters."
                )

        if errors:
            message = "; ".join(errors)
            logger.error(message)
            raise ValueError(message)

        # Build argument list performing conversions
        ordered_argument_values = []
        for idx, exp_name in enumerate(expected_names_in_order):
            lower = exp_name.lower()
            definition = param_defs_by_lower[lower]
            direction = (definition.get("direction") or "IN").upper()
            data_type = definition.get("data_type") or ""
            has_default = definition.get("default_value") is not None

            if direction == "OUT":
                # Not bound in CALL argument list
                continue

            if lower in provided_lower_to_value:
                raw_val = provided_lower_to_value[lower]
                converted = _convert_value(raw_val, data_type, exp_name)
                ordered_argument_values.append(converted)
            else:
                # Not provided: only legal if trailing or has default
                if idx > last_provided_index and has_default:
                    # Omit argument to leverage trailing defaults by truncating at the first missing trailing
                    break
                # If not trailing, we must include something; raise (should have been caught earlier)
                message = f"Parameter '{exp_name}' is required or non-trailing default cannot be omitted."
                logger.error(message)
                raise ValueError(message)

        # Construct CALL with the number of placeholders equal to length of ordered_argument_values
        placeholders = ", ".join(["?"] * len(ordered_argument_values))
        qualified_name = f'"{procedure_schema}"."{procedure_name}"'
        sql = (
            f"CALL {qualified_name}({placeholders})"
            if placeholders
            else f"CALL {qualified_name}()"
        )

        logger.debug(
            "Executing: %s | arg_count=%d | args=%s",
            sql,
            len(ordered_argument_values),
            ordered_argument_values,
        )
        with self.connection.cursor() as cursor:
            cursor.execute(sql, tuple(ordered_argument_values))
            rows_affected = getattr(cursor, "rowcount", -1)
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            result = [dict(zip(columns, row)) for row in rows]

        return {
            "message": f"Executed {procedure_schema}.{procedure_name} successfully.",
            # "rows_affected": rows_affected,
            "result": result,
        }
