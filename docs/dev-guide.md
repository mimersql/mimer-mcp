---
hide:
  - navigation
---

## Project Structure
```
mimer-mcp/
├── src/
│   └── mimer_mcp_server/           # Main package directory
│       ├── __init__.py
│       ├── config.py               # Configuration and environment variables
│       ├── server.py               # MCP server setup and tool registration
│       ├── database/               # Database modules
│       │   ├── __init__.py
│       │   ├── connection.py       # Database connection pool management
│       │   ├── ddl_generator.py    # DDL generation utilities
│       │   ├── schema_inspector.py # Schema inspection tools
│       │   └── stored_procedure_manager.py  # Stored procedure management
│       └── utils/                  # Utility modules
│           ├── __init__.py
│           └── utils.py
├── tests/                          # Test files
├── docs/                           # Documentation and images
│   └── images/                     # Screenshot assets
├── .env.example                    # Environment variables template
├── .gitignore
├── .python-version                 # Python version specification
├── Dockerfile						# Docker configuration
├── pyproject.toml                  # Project configuration and dependencies
├── README.md                       # This file
├── entrypoint.sh					# Docker entrypoint script
├── LICENSE
├── requirements.txt                # Alternative dependency list
└── uv.lock                         # Dependency lock file
```

## Prerequisites
- Python: 3.10+
- [uv](https://github.com/astral-sh/uv): for dependency management and running the server
- Mimer SQL: Access to a running Mimer SQL database
- Node.js and npm: for debugging with MCP inspector

### Install `uv`
```sh
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# or via Homebrew
brew install uv
```

Verify installation:
```sh
uv --version
```

### Install Node.js and npm
```sh
# Linux (Ubuntu/Debian)
sudo apt install nodejs npm

# macOS (via Homebrew)
brew install node
```

Verify installation:
```sh
node --version
npm --version
```

## Getting Started
1. Clone the repository

2. Create and activate a virtual environment
```sh
uv venv

# macOS / Linux
source .venv/bin/activate
# Windows
.venv\Scripts\activate
```

3. Install dependencies from pyproject.toml
```sh
uv sync
```

4. Configure environment variables
```sh
cp .env.example .env
# Edit .env with your database credentials
```
The configuration is loaded automatically via `config.py`.

## Debug with MCP inspector

MCP Inspector provides a web interface for testing and debugging MCP Tools (Requires Node.js: 22.7.5+):
```sh
npx @modelcontextprotocol/inspector
```

!!! note

    MCP Inspector is a Node.js app and the npx command allows running MCP Inspector without having to permanently install it as a Node.js package. 

Alternatively, you can use FastMCP CLI to start the MCP inspector
```sh
uv run fastmcp dev /absolute/path/to/server.py
```

## Running Tests

To run all tests in the `tests/` directory:
```sh
pytest tests/
```

To run tests in a specific module:
```sh
pytest tests/test_server.py
```