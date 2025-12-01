import requests
import json
import uuid

# MCP server configuration
MCP_SERVER_URL = "http://localhost:3333/mcp"

def initialize_session():
    """
    Initialize an MCP session and return the session ID.
    
    Returns:
        Session ID string or None if failed
    """
    payload = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "mcp-python-client",
                "version": "1.0.0"
            }
        }
    }
    
    try:
        response = requests.post(
            MCP_SERVER_URL,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream"
            },
            stream=True,
            timeout=(5, 10)  # (connect timeout, read timeout)
        )
        response.raise_for_status()
        
        # Get session ID from response headers
        session_id = response.headers.get('mcp-session-id')
        
        # Read the SSE stream to complete initialization
        init_complete = False
        try:
            for line in response.iter_lines(decode_unicode=True):
                if line:
                    if line.startswith('data: '):
                        data = line[6:]
                        try:
                            init_response = json.loads(data)
                            if "result" in init_response:
                                print(f"Session initialized: {session_id}")
                                print(f"Server info: {init_response['result'].get('serverInfo', {})}")
                                init_complete = True
                                break
                        except json.JSONDecodeError:
                            continue
        except requests.exceptions.ChunkedEncodingError:
            # This is expected when the server keeps the connection open
            pass
        
        if session_id and init_complete:
            # Send initialized notification
            send_initialized_notification(session_id)
            return session_id
        elif session_id:
            print(f"Session ID obtained: {session_id}")
            # Try sending initialized notification anyway
            send_initialized_notification(session_id)
            return session_id
        else:
            print("No session ID in response")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Session initialization failed: {e}")
        return None

def send_initialized_notification(session_id):
    """
    Send the initialized notification after successful initialization.
    
    Args:
        session_id: MCP session ID
    """
    payload = {
        "jsonrpc": "2.0",
        "method": "notifications/initialized"
    }
    
    try:
        response = requests.post(
            MCP_SERVER_URL,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "mcp-session-id": session_id
            },
            timeout=5
        )
        if response.status_code == 200:
            print("Initialized notification sent successfully")
    except:
        # Notifications might not require a response
        pass

def call_mcp_tool(session_id, tool_name, arguments=None):
    """
    Call an MCP tool with a session ID.
    
    Args:
        session_id: MCP session ID
        tool_name: Name of the tool to call
        arguments: Dictionary of arguments (optional)
    
    Returns:
        The tool's response
    """
    if arguments is None:
        arguments = {}
    
    # Generate a unique request ID
    request_id = str(uuid.uuid4())
    
    # MCP uses JSON-RPC 2.0 format
    payload = {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        }
    }
    
    try:
        # Send request with session ID
        response = requests.post(
            MCP_SERVER_URL,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "mcp-session-id": session_id
            },
            stream=True,
            timeout=(5, 10)
        )
        
        response.raise_for_status()
        
        # Parse SSE response
        result_data = None
        try:
            for line in response.iter_lines(decode_unicode=True):
                if line:
                    if line.startswith('data: '):
                        data = line[6:]  # Remove 'data: ' prefix
                        try:
                            result_data = json.loads(data)
                            # Check for JSON-RPC errors
                            if "error" in result_data:
                                print(f"Error: {result_data['error']}")
                                return None
                            if "result" in result_data:
                                return result_data["result"]
                        except json.JSONDecodeError:
                            continue
        except requests.exceptions.ChunkedEncodingError:
            # Expected when server keeps connection open
            pass
        
        return result_data
    
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None

# Convenience functions for each tool

def list_schemas(session_id):
    """List all available schemas in the database."""
    return call_mcp_tool(session_id, "list_schemas")

def list_table_names(session_id, schema):
    """List table names from the specified schema."""
    return call_mcp_tool(session_id, "list_table_names", {"schema": schema})

def get_table_info(session_id, table_names, schema, sample_size=3):
    """Get detailed table schemas and sample rows."""
    return call_mcp_tool(session_id, "get_table_info", {
        "table_names": table_names,
        "schema": schema,
        "sample_size": sample_size
    })

def execute_query(session_id, query, params=None):
    """Execute a SQL SELECT query and return the results."""
    return call_mcp_tool(session_id, "execute_query", {
        "query": query,
        "params": params or []
    })

def list_stored_procedures(session_id):
    """List all stored procedures in the database."""
    return call_mcp_tool(session_id, "list_stored_procedures")

def get_stored_procedure_definition(session_id, procedure_schema, procedure_name):
    """Get the definition of a stored procedure."""
    return call_mcp_tool(session_id, "get_stored_procedure_definition", {
        "procedure_schema": procedure_schema,
        "procedure_name": procedure_name
    })

def get_stored_procedure_parameters(session_id, procedure_schema, procedure_name):
    """Get the parameters of a stored procedure."""
    return call_mcp_tool(session_id, "get_stored_procedure_parameters", {
        "procedure_schema": procedure_schema,
        "procedure_name": procedure_name
    })

def execute_stored_procedure(session_id, procedure_schema, procedure_name, parameters):
    """Execute a stored procedure in the database."""
    # Convert parameters dict to JSON string if needed
    if isinstance(parameters, dict):
        parameters = json.dumps(parameters)
    
    return call_mcp_tool(session_id, "execute_stored_procedure", {
        "procedure_schema": procedure_schema,
        "procedure_name": procedure_name,
        "parameters": parameters
    })

def main():
    """Example usage of all MCP tools."""
    
    print("Initializing MCP session...")
    print("-" * 50)
    
    # Initialize session
    session_id = initialize_session()
    if not session_id:
        print("Failed to initialize session")
        return
    
    print()
    
    # Example 1: List all schemas
    print("=" * 60)
    print("1. Listing all schemas...")
    print("=" * 60)
    schemas = list_schemas(session_id)
    print(json.dumps(schemas.get("structuredContent"), indent=2))
    print()
    
    # Example 2: List tables in first schema
    if schemas and "structuredContent" in schemas and schemas["structuredContent"]["result"]:
        schema_name = schemas["structuredContent"]["result"][0]
        print("=" * 60)
        print(f"2. Listing tables in schema '{schema_name}'...")
        print("=" * 60)
        tables = list_table_names(session_id, schema_name)
        print(json.dumps(tables.get("structuredContent"), indent=2))
        print()
        
        # Example 3: Get table info
        if tables and "structuredContent" in tables and tables["structuredContent"]["result"]:
            table_list = tables["structuredContent"]["result"][:2]  # Get first 2 tables
            print("=" * 60)
            print(f"3. Getting info for tables: {table_list}")
            print("=" * 60)
            table_info = get_table_info(session_id, table_list, schema_name, sample_size=2)
            if table_info and "content" in table_info:
                print(table_info["content"][0]["text"])
            print()
    
    # Example 4: Execute a simple query
    query_table = tables.get("structuredContent")["result"][0] if tables and "structuredContent" in tables else "INFORMATION_SCHEMA.TABLES"
    query = f"SELECT * FROM {query_table}"
    print("=" * 60)
    print(f"4. Executing {query}...")
    print("=" * 60)

    result = execute_query(session_id, query)
    print(json.dumps(result.get("structuredContent"), indent=2))
    print()
    
    # Example 5: List stored procedures
    print("=" * 60)
    print("5. Listing stored procedures...")
    print("=" * 60)
    procedures = list_stored_procedures(session_id)
    print(json.dumps(procedures.get("structuredContent"), indent=2))
    print()
    
    # Example 6: Get stored procedure details (if any exist)
    if procedures and "structuredContent" in procedures and procedures["structuredContent"]["result"]:
        proc = procedures["structuredContent"]["result"][0]
        proc_schema = proc["procedure_schema"]
        proc_name = proc["procedure_name"]
        
        print("=" * 60)
        print(f"6. Getting definition for procedure {proc_schema}.{proc_name}...")
        print("=" * 60)
        definition = get_stored_procedure_definition(session_id, proc_schema, proc_name)
        if definition and "content" in definition:
            print(definition["content"][0]["text"])
        print()
        
        print("=" * 60)
        print(f"7. Getting parameters for procedure {proc_schema}.{proc_name}...")
        print("=" * 60)
        params = get_stored_procedure_parameters(session_id, proc_schema, proc_name)
        print(json.dumps(params.get("structuredContent"), indent=2))
        print()

if __name__ == "__main__":
    main()
