## Overview
<!-- --8<-- [start:overview] -->
The Mimer MCP server provides you with access to database tools such as:

**Database Schema Tools**

- `list_schemas` — View all available schemas in the connected database
- `list_table_names` — List table names within a specified schema
- `get_table_info` — Get detailed information about a table, including its schema and sample rows

**Query Execution Tools**

- `execute_query` — Run SQL SELECT queries with parameter support for safe, read-only operations

**Stored Procedure Tools**

- `list_stored_procedures` — List read-only stored procedures
- `get_stored_procedure_definition` — Get the definition of a stored procedure
- `get_stored_procedure_parameters` — Check what parameters a stored procedure expects
- `execute_stored_procedure` — Run a stored procedure with JSON-formatted parameters
<!-- --8<-- [end:overview] -->


## Understanding Tool Results

Mimer MCP Server is built on [FastMCP](https://gofastmcp.com/getting-started/welcome), an open-source Python framework, which provides enhanced response structures beyond standard MCP. When you call a tool, you get a `CallToolResult` object that includes both FastMCP-specific and standard MCP properties.

### Key Properties

| Properties  | Type         | Description |
| ----------- | ------------ | ----------- |
| `.data`       | `Any` |**FastMCP exclusive**: Fully hydrated Python objects with complex type support (datetimes, UUIDs, custom classes). Goes beyond JSON to provide complete object reconstruction from output schemas. |
| `.content`       | `list[mcp.types.ContentBlock]` | Standard MCP content blocks (`TextContent`, `ImageContent`, `AudioContent`, etc.) available from all MCP servers.  |
| `.structured_content`    | `dict[str, Any] | None` | Standard MCP structured JSON data as sent by the server, available from all MCP servers that support structured outputs.  |
| `.is_error`    | `bool` | Boolean indicating if the tool execution failed. |

*Source: [FastMCP - Handling Tool Results](https://gofastmcp.com/clients/tools#handling-results)*

In the below section, we focuse on the `.structured_content` property, which contains the JSON data returned by each tool. For complete details on working with `CallToolResult` objects, see the [FastMCP documentation](https://gofastmcp.com/clients/tools).


## Available Tools

### Database Schema Tools

**list_schemas**

This tool retrieves a complete list of all schemas (databases) available in the connected Mimer SQL instance. It provides visibility into the database structure and helps you identify which schemas are available for further exploration and querying.

!!! example annotate "Example prompts that may invoke this tool (1)" 

    ```
    List all schemas in the database
    ```

    ```
    Show me what schemas are available
    ```

    ```
    What schemas exist in this Mimer SQL database?
    ```

1. Note: Tool selection by the LLM is non-deterministic and depends on the specific model, prompt phrasing, and conversation context. The same prompt may result in different tool choices across different LLM interactions.

**Tool description**

#### ::: mimer_mcp_server.server.list_schemas

**Response example** :material-information-outline:{ title="This example uses Mimer's Example Database and may be truncated for brevity." }
```json
{
  "result": [
    "mimer_store",
    "mimer_store_book",
    "mimer_store_music",
    "mimer_store_web"
  ]
}
```

---

**list_table_names**

This tool retrieves all table names from a specific schema in the database. It filters out system tables and only returns base tables (user-created tables). This is useful for discovering what data tables exist within a particular schema before querying or examining them in detail.


!!! example annotate "Example prompts that may invoke this tool (1)" 

    ```
    List all tables in the <your-schema> schema
    ```

    ```
    Show me tables in <your-schema>
    ```

    ```
    What tables exist in the <your-schema> schema?
    ```

1. Note: Tool selection by the LLM is non-deterministic and depends on the specific model, prompt phrasing, and conversation context. The same prompt may result in different tool choices across different LLM interactions.

**Tool description**

#### ::: mimer_mcp_server.server.list_table_names

**Response example** :material-information-outline:{ title="This example uses Mimer's Example Database and may be truncated for brevity." }
```json
{
  "result": [
    "categories",
    "countries",
    "currencies",
    "customers",
    "formats",
    "images",
    "items",
    "order_items",
    "orders",
    "producers",
    "products",
  ]
}
```

---

**get_table_info**

This tool provides comprehensive information about specified tables, including their complete DDL (Data Definition Language) schema and sample rows. It's ideal for understanding table structure, column types, constraints, and getting a preview of the actual data stored in the tables.


!!! example annotate "Example prompts that may invoke this tool (1)" 

    ```
    Get information about the <your-table> table in <your-schema> schema
    ```

    ```
    Show me the structure and sample data for <your-table-a> and <your-table-b> tables
    ```

    ```
    Get table info for <your-table> with <no-of-sample> sample rows
    ```

1. Note: Tool selection by the LLM is non-deterministic and depends on the specific model, prompt phrasing, and conversation context. The same prompt may result in different tool choices across different LLM interactions.

**Tool description**

#### ::: mimer_mcp_server.server.get_table_info

**Response example** :material-information-outline:{ title="This example uses Mimer's Example Database and may be truncated for brevity." }
```json
{
  "result": "CREATE TABLE \"customers\" (\n    \"customer_id\" INTEGER(5) DEFAULT NEXT_VALUE OF \"mimer_store\".\"customer_id_seq\" NOT NULL,\n    \"title\" CHARACTER VARYING(6),\n    \"surname\" CHARACTER VARYING(48) NOT NULL,\n    \"forename\" CHARACTER VARYING(24) NOT NULL,\n    \"date_of_birth\" DATE,\n    \"address_1\" CHARACTER VARYING(48) NOT NULL,\n    \"address_2\" CHARACTER VARYING(48),\n    \"town\" CHARACTER VARYING(32) NOT NULL,\n    \"postcode\" CHARACTER VARYING(12) NOT NULL,\n    \"country_code\" CHARACTER(2) NOT NULL,\n    \"email\" CHARACTER VARYING(128),\n    \"password\" CHARACTER VARYING(18),\n    \"registered\" DATE DEFAULT CURRENT_DATE,\n    \"last_order\" TIMESTAMP(0) DEFAULT NULL,\n    PRIMARY KEY (\"customer_id\"),\n    FOREIGN KEY(\"country_code\") REFERENCES \"mimer_store\".\"countries\" (\"code\"),\n    CONSTRAINT \"cst_email_exists\" UNIQUE (\"email\")\n)\n/* No rows in customers table */"
}
```

---

### Query Execution Tools

**execute_query**

This tool allows you to execute read-only SQL SELECT queries against the connected database. It returns results as a list of dictionaries, where each dictionary represents a row with column names as keys. For security reasons, this tool only accepts SELECT statements and will reject any data modification queries (INSERT, UPDATE, DELETE, etc.).


!!! example annotate "Example prompts that may invoke this tool (1)" 

    ```
    Get the top 10 orders by total amount
    ```

1. Note: Tool selection by the LLM is non-deterministic and depends on the specific model, prompt phrasing, and conversation context. The same prompt may result in different tool choices across different LLM interactions.

**Tool description**

#### ::: mimer_mcp_server.server.execute_query

**Response example** :material-information-outline:{ title="This example uses Mimer's Example Database and may be truncated for brevity." }
```json
{
  "result": [
    {
      "product": "'Murder in the Cathedral'",
      "product_id": 30619
    },
    {
      "product": "'Reave the Just' and Other Tales",
      "product_id": 30620
    },
    {
      "product": "100 Anos",
      "product_id": 30001
    },
    {
      "product": "12 Golden Country Greats",
      "product_id": 30002
    }
  ]
}
```

!!! warning "Security Note"
    Only SELECT queries are permitted. This ensures that the tool cannot be used to modify, delete, or corrupt data in the database.

---

### Stored Procedure Tools

**list_stored_procedures**

This tool retrieves a list of all stored procedures that have 'READS SQL DATA' access level. These are read-only procedures that can safely query data without modifying it. The tool returns both the schema and name of each procedure, making it easy to identify and subsequently call specific procedures.


!!! example annotate "Example prompts that may invoke this tool (1)" 

    ```
    What stored procedures can I call?
    ```

    ```
    Show me available procedures in the database
    ```

    ```
    List all stored procedures
    ```

1. Note: Tool selection by the LLM is non-deterministic and depends on the specific model, prompt phrasing, and conversation context. The same prompt may result in different tool choices across different LLM interactions.

**Tool description**

#### ::: mimer_mcp_server.server.list_stored_procedures

**Response example** :material-information-outline:{ title="This example uses Mimer's Example Database and may be truncated for brevity." }
```json
{
  "result": [
    {
      "procedure_schema": "mimer_store",
      "procedure_name": "barcode",
      "remark": "Result set procedure that returns book or music details for the given EAN"
    },
    {
      "procedure_schema": "mimer_store",
      "procedure_name": "coming_soon",
      "remark": "Result set procedure that returns items that will be release in the next month"
    },
    {
      "procedure_schema": "mimer_store_book",
      "procedure_name": "search",
      "remark": null
    },
    {
      "procedure_schema": "mimer_store_book",
      "procedure_name": "title_details",
      "remark": "Result set procedure that returns book details"
    }
  ]
}
```

---

**get_stored_procedure_definition**

This tool returns the full Data Definition Language (DDL) statement for a specified stored procedure. This is useful for understanding what the procedure does, what logic it contains, and how it's implemented before executing it.


!!! example annotate "Example prompts that may invoke this tool (1)" 

    ```
    What does the get_product_inventory procedure do?
    ```

    ```
    Show me the definition of <procedure-name> procedure in <procedure-schema> schema
    ```

1. Note: Tool selection by the LLM is non-deterministic and depends on the specific model, prompt phrasing, and conversation context. The same prompt may result in different tool choices across different LLM interactions.

**Tool description**

#### ::: mimer_mcp_server.server.get_stored_procedure_definition

**Response example** :material-information-outline:{ title="This example uses Mimer's Example Database and may be truncated for brevity." }
```json
{
  "result": "CREATE PROCEDURE \"mimer_store_book\".\"search\"(IN p_book_title VARCHAR(48),\n                                         IN p_author VARCHAR(48))\nVALUES (VARCHAR(48), VARCHAR(128), VARCHAR(20), DECIMAL(7, 2), INTEGER)\nAS (title, authors_list, format, price, item_id)\nSPECIFIC sp_search\nREADS SQL DATA\nBEGIN\n   DECLARE data ROW AS (mimer_store_book.details(title, authors_list, format,\n                                                 price, item_id, product_id,\n                                                 display_order));\n   DECLARE c_1 CURSOR FOR SELECT DISTINCT \n                                 title, authors_list, format,\n                                 price, item_id, product_id,\n                                 display_order\n                             FROM mimer_store_book.details\n                             JOIN mimer_store_book.authors USING (item_id)\n                             JOIN mimer_store_book.keywords USING (keyword_id)\n                             WHERE title_search LIKE TRIM(TRAILING '0' FROM\n                                mimer_store.product_search_code(p_book_title))\n                                || '%'\n                             AND keyword LIKE REPLACE(\n                                mimer_store_book.authors_name(p_author),\n                                ',', '%,')\n                                || '%'\n                             ORDER BY title, authors_list, product_id,\n                                      display_order;\n\n   DECLARE EXIT HANDLER FOR NOT FOUND\n      CLOSE c_1;\n\n   OPEN c_1;\n\n   LOOP\n      FETCH c_1\n         INTO data;\n\n      RETURN (data.title, data.authors_list, data.format, data.price,\n              data.item_id);\n   END LOOP;\nEND  -- of routine mimer_store_book.search"
}
```

---

**get_stored_procedure_parameters**

This tool retrieves detailed information about all parameters required by a stored procedure, including their names, data types, and modes (IN, OUT, INOUT). This is essential for understanding how to properly call a procedure with the correct arguments.

**Tool description**

#### ::: mimer_mcp_server.server.get_stored_procedure_parameters

**Response example** :material-information-outline:{ title="This example uses Mimer's Example Database and may be truncated for brevity." }
```json
{
  "procedure_schema": "mimer_store_book",
  "procedure_name": "search",
  "parameters": [
    {
      "p_book_title": {
        "data_type": "CHARACTER VARYING(48)",
        "direction": "IN",
        "default_value": null
      }
    },
    {
      "title": {
        "data_type": "CHARACTER VARYING(48)",
        "direction": "OUT",
        "default_value": null
      }
    },
    {
      "p_author": {
        "data_type": "CHARACTER VARYING(48)",
        "direction": "IN",
        "default_value": null
      }
    },
    {
      "authors_list": {
        "data_type": "CHARACTER VARYING(128)",
        "direction": "OUT",
        "default_value": null
      }
    },
    {
      "item_id": {
        "data_type": "INTEGER(10)",
        "direction": "OUT",
        "default_value": null
      }
    }
  ]
}
```

---

**execute_stored_procedure**

This tool executes a stored procedure in the database with the provided parameters. It's recommended to use `list_stored_procedures` first to discover available procedures, then `get_stored_procedure_parameters` to understand what parameters are needed before calling this tool.

**Tool description**

#### ::: mimer_mcp_server.server.execute_stored_procedure

**Response example** :material-information-outline:{ title="This example uses Mimer's Example Database and may be truncated for brevity." }
```json
{
  "message": "Executed mimer_store.barcode successfully.",
  "result": [
    {
      "title": "100 Anos",
      "creator": "Carlos Gardel",
      "format": "Audio CD",
      "price": "9.98",
      "item_id": 60001
    }
  ]
}
```