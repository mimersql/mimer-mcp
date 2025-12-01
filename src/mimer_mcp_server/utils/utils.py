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

from typing import List, Tuple, Dict, Any


def parse_domains(ddl: str) -> List[Tuple[str, str]]:
    """Parse domain names from DDL string.

    Args:
        ddl: The DDL string containing CREATE DOMAIN statements.

    Returns:
        A list of tuples (schema, domain_name) for each detected domain.

    """

    import re

    # Pattern matches "schema"."name"
    pattern = r'"([^"]+)"\."([^"]+)"'

    # Use finditer to get spans to inspect the context before each match
    raw_matches = [
        (m.group(1), m.group(2), m.start()) for m in re.finditer(pattern, ddl)
    ]

    filtered: List[Tuple[str, str]] = []
    for schema, name, start_idx in raw_matches:
        # Exclude occurrences that appear immediately after a REFERENCES clause
        # e.g., ... REFERENCES "schema"."table" ("col")
        before = ddl[:start_idx]
        # Trim trailing whitespace and opening parens that may appear between
        # REFERENCES and the opening quote
        trimmed = re.sub(r"[\s(]*$", "", before)
        # Ignore foreign key targets and sequence names after NEXT VALUE/OF
        if re.search(
            r"(?i)(REFERENCES|NEXT\s+VALUE\s+(OF|FOR)|NEXT_VALUE\s+OF)$", trimmed
        ):
            continue
        filtered.append((schema, name))

    # Return unique domain names as a list of tuples (schema, domain_name)
    return list(set(filtered))


def format_sql_type(col: Dict[str, Any]) -> str:
    """Format SQL data type with precision and scale values.

    Converts column metadata into a formatted SQL data type string,
    including appropriate precision, scale, and length parameters.

    Args:
        col: Column dictionary with data_type, character_maximum_length,
                 numeric_precision, numeric_scale, datetime_precision

    Returns:
        Formatted SQL type string (e.g., 'VARCHAR(50)', 'DECIMAL(10,2)')

    Example:
        >>> col = {
        ...     'data_type': 'CHARACTER VARYING',
        ...     'character_maximum_length': 50,
        ...     'numeric_precision': None,
        ...     'numeric_scale': None,
        ...     'datetime_precision': None
        ... }
        >>> format_data_type(col)
        'CHARACTER VARYING(50)'
    """
    data_type = col["data_type"]
    char_max_length = col["character_maximum_length"]
    numeric_precision = col["numeric_precision"]
    numeric_scale = col["numeric_scale"]
    datetime_precision = col["datetime_precision"]

    # Handle CHARACTER types
    if data_type in [
        "CHARACTER",
        "CHARACTER VARYING",
        "NATIONAL CHARACTER",
        "NATIONAL CHARACTER VARYING",
    ]:
        if char_max_length is not None:
            return f"{data_type}({char_max_length})"
        return data_type

    # Handle DECIMAL
    elif data_type == "DECIMAL":
        if numeric_precision is not None and numeric_scale is not None:
            return f"DECIMAL({numeric_precision},{numeric_scale})"
        elif numeric_precision is not None:
            return f"DECIMAL({numeric_precision})"
        return data_type

    # Handle INTEGER
    elif data_type == "INTEGER":
        if numeric_precision is not None:
            return f"INTEGER({numeric_precision})"
        return data_type

    # Handle BINARY
    elif data_type == "BINARY":
        if char_max_length is not None:
            return f"BINARY({char_max_length})"
        return data_type

    # Handle TIME and TIMESTAMP
    elif data_type in ["TIME", "TIMESTAMP"]:
        if datetime_precision is not None:
            return f"{data_type}({datetime_precision})"
        return data_type

    # Default case - return as is
    return data_type
