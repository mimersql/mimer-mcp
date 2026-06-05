# Changelog

## 1.1.0

### Changed

- **FastMCP upgraded from 2.13.1 to 3.2.4**
    The core MCP framework dependency has been upgraded to the FastMCP 3.x release line. All tool names, parameter signatures, and return types are unchanged — existing MCP clients require no updates.
- **MCP protocol package upgraded from 1.22.0 to 1.27.0**
    The underlying `mcp` SDK dependency has been updated to align with FastMCP 3.x requirements.
- **Stronger SELECT-only enforcement with MimerPy 1.3.9**
    Added configurable `DB_READONLY` and upgrade to MimerPy 1.3.9 to use native read-only enforcement to prevent write operations at the driver/connection level.

### Added

- **Database administration tools**
    - `list_indexes` - List all indexes in a specified schema, including both implicit and explicit indexes
    - `create_index` - Create secondary indexes on table columns to improve query performance (only enabled when `DB_READONLY=false`)
    - `get_query_plan` - Generate and display query optimization plans for SQL statements
    - `get_database_stats` - Retrieve comprehensive database statistics and runtime information using MIMINFO and SQLMONITOR
- **SQL optimization prompt**
    - `query_optimization` - Prompt for analyzing, optimizing, and validating SQL query performance
- **Tool behavior annotations added for MCP clients**
    MCP clients like Claude and ChatGPT use annotation hints to determine when to skip confirmation prompts and how to present tools to users. Therefore, annotations are recommended to give MCP clients hints to understand tool safety profiles and make better execution decisions. FastMCP `ToolAnnotations` are added across server tools to expose behavior hints (`readOnlyHint`, `idempotentHint`, `openWorldHint`, and `destructiveHint` where applicable). Read-only tools now advertise read-safe behavior, `create_index` uses a shared reversible-write annotation profile, and `execute_query` is conditionally annotated as read-only in readonly mode or potentially destructive in write-enabled mode.
- **Progress reporting and timeout for `execute_query`**
    - `execute_query` now emits indeterminate progress notifications (before and after query execution) so clients that send a `progressToken` can surface a "working…" indicator during long-running queries.
    - `execute_query` now enforces a 5-minute hard timeout (`timeout=300.0`) via the `@mcp.tool` decorator. Queries that exceed the limit return MCP error code `-32000` instead of blocking the server indefinitely.
- **Write tools disabled via tag visibility**
    `create_index` and other write tools are now tagged `tags={"write"}`. When `DB_READONLY=true`, all write-tagged tools are disabled at startup with `mcp.disable(tags={"write"})`.

### Fixed

- **SQL injection and identifier quoting hardening**
    Applied `quote_ident()` to `create_index` identifiers (`schema`, `table`, `index_name`, `columns`) and stored procedure qualified names, and hardened `_get_sample_rows` by quoting `schema` and `table_name` and binding `limit` as a parameter. Added unit tests in `tests/test_index_manager.py`, `tests/test_schema_inspector.py`, and `tests/test_stored_procedure_manager.py`.
- **Stored procedure execution and definition lookup robustness**
    Fixed `execute_stored_procedure` to safely handle procedures that return no result set (`cursor.description is None`) by returning an empty `result` list instead of crashing. Fixed `get_stored_procedure_definition` to raise an explicit `ValueError` when no definition is found in either metadata source, preventing implicit `None` returns. Added regression tests in `tests/test_stored_procedure_manager.py`.

## 1.0.0

### Added

- **Initial public release** of Mimer MCP Server
- MCP server implementation using FastMCP
- Database connectivity tools:
    - `execute_query` - Execute SQL SELECT queries
    - `list_schemas` - List all available database schemas
    - `list_table_names` - List tables in a schema
    - `get_table_info` - Get detailed table schemas with sample data
- Stored procedure support:
    - `list_stored_procedures` - List all stored procedures
    - `get_stored_procedure_definition` - Get procedure definitions
    - `get_stored_procedure_parameters` - Get procedure parameters
    - `execute_stored_procedure` - Execute stored procedures
- Docker support with Dockerfile and `docker-compose.yml`
- stdio and HTTP transport support
- Documentation with MkDocs