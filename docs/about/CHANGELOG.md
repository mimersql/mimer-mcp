# Changelog

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