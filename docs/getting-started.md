---
hide:
  - navigation
---

# Getting Started with Mimer MCP Server

## Prerequisites

- Python 3.10 or later (with uv installed) _or_ Docker
- Mimer SQL 11.0 or later

---

Before running the server, you need to configure your database connection settings using environment variables. The Mimer MCP Server reads these from a `.env` file.

## Setting Up Your Environment File

An example configuration file is provided in `.env.example` (See [GitHub Repo](https://github.com/mimersql/mimer-mcp/blob/main/.env.example)). You can copy the example configuration file to create your own `.env` file:

```bash
cp .env.example .env
```

Then edit the `.env` file with your database credentials and preferences.

### Configuration Options 

| Environment Variable | Default | Description |
|----------------------|---------|-------------|
| `DB_DSN` | _Required_ | Database name to connect to |
| `DB_USER` | _Required_ | Database username |
| `DB_PASSWORD` | _Required_ | Database password |
| `DB_HOST` | `localhost` | Database host address (use `host.docker.internal` when database runs on host and MCP server runs in Docker) |
| `DB_PORT` | `1360` | Database port number |
| `DB_PROTOCOL` | `tcp` | Connection protocol |
| `DB_POOL_INITIAL_CON` | `0` | Initial number of idle connections in the pool |
| `DB_POOL_MAX_UNUSED` | `0` | Maximum number of unused connections in the pool |
| `DB_POOL_MAX_CON` | `0` | Maximum number of connections allowed (0 = unlimited) |
| `DB_POOL_BLOCK` | `false` | Determines behavior when exceeding the maximum number of connections. If `true`, block and wait for a connection to become available; if `false`, raise an error when maxconnections is exceeded |
| `DB_POOL_DEEP_HEALTH_CHECK` | `true` | If `true`, validates connection health before getting from pool (slower but more reliable) |
| `MCP_LOG_LEVEL` | `INFO` | Logging level for the MCP server. Options: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |

---

## Getting Started with VS Code

MCP servers are configured using a JSON file (`mcp.json`). Different MCP hosts may have slightly different configuration formats. In this guide, we'll focus on VS Code as an example. First, ensure you've installed the latest version of VS Code and have access to Copilot.

In VS Code, the configuration file is located at `.vscode/mcp.json` in your workspace. You have two options for running the server: using Docker for an isolated environment, or using Python with uv.

### Option 1: Using Docker (Recommended)

Docker provides an isolated environment and simplifies deployment across different systems.

=== "Option 1.1: Use Docker Compose and Official Mimer SQL Docker Container"

	!!! tip
		This is ideal for quickly getting started without installing Mimer SQL locally.

	 It will start a Mimer SQL Docker container as well as the `mimer-mcp-server` container, set up a private network between the two containers and create the Mimer SQL example database. The Mimer SQL database will be stored in the docker volume called `mimer_mcp_data` so that database changes are persistent.

	Simply, create a file named `mcp.json` in the `.vscode` folder of your workspace with this configuration:

	```json5 title="mcp.json"
	{
		"servers": {
			"mimer-mcp-server": {
				"command": "docker",
				"args": [
					"compose",
					"run",
					"--rm",
					"-i",
					"--no-TTY",
					"mimer-mcp-server"
				]
			}
		},
		"inputs": []
	}
	```

	This option uses the `.env_docker_compose` file included in the repository with pre-configured settings for the example database. See [Configuration Options documentation](#configuration-options) for more details.

=== "Option 1.2: Use the Official Image from Docker Hub"

	Mimer provides a pre-built image on Docker Hub that you can use without building locally. Docker will automatically pull the image when you first run the container.

	Simply, create a file named `mcp.json` in the `.vscode` folder of your workspace with this configuration:

	```json5 title="mcp.json"
	{
		"servers": {
			"mimer-mcp-server": {
				"command": "docker",
				"args": [
					"run",
					"-i",
					"--rm",
					"--add-host=host.docker.internal:host-gateway", // (1)!
					"--env-file=/absolute/path/to/.env", // (2)!
					"mimersql/mimer-mcp:latest",
				]
			}
		},
		"inputs": []
	}
	```

	1. The `--add-host=host.docker.internal:host-gateway` flag allows the Docker container to connect to your Mimer database running on the host machine.

	2. Replace `/absolute/path/to/.env` with the actual absolute path to your environment configuration file. See [Configuration Options documentation](#configuration-options)  for more details.

	!!! warning "Limitation: Rootless Docker"
		Running the MCP server in rootless Docker mode may cause network connectivity issues when connecting to the database. If you encounter connection problems, please use standard Docker with root privileges or consider using the "Option 1.1: Use Docker compose and the official Mimer SQL docker container" or "Option 2: Python setup" instead.

===	"Option 1.3: Build the Docker Image Locally"

	Run the following command in the project directory:

	```bash
	docker build -t mimer-mcp-server .
	```

	This creates a Docker image named `mimer-mcp-server` that contains everything needed to run the server.

	Next, create a file named `mcp.json` in the `.vscode` folder of your workspace with this configuration:

	```json title="mcp.json"
	{
		"servers": {
			"mimer-mcp-server": {
				"command": "docker",
				"args": [
					"run",
					"-i",
					"--rm",
					"--add-host=host.docker.internal:host-gateway", // (1)!
					"--env-file=/absolute/path/to/.env", // (2)!
					"mimer-mcp-server"
				]
			}
		},
		"inputs": []
	}
	```

	1. The `--add-host=host.docker.internal:host-gateway` flag is only needed if your Mimer SQL database is running on your host machine (not in a container). When used, set `DB_HOST=host.docker.internal` in your `.env` file instead of `localhost`.

	2. Replace `/absolute/path/to/.env` with the actual absolute path to your environment configuration file on your host machine. The `--env-file` flag loads environment variables from your `.env` file into the container. See [Configuration Options documentation](#configuration-options) for more details.

	!!! warning "Limitation: Rootless Docker"
		Running the MCP server in rootless Docker mode may cause network connectivity issues when connecting to the database. If you encounter connection problems, please use standard Docker with root privileges or consider using the "Option 1.1: Use Docker compose and the official Mimer SQL docker container" or "Option 2: Using Python with uv" instead.

### Option 2: Using Python (with uv)

If you prefer a setup without Docker, you can run the server directly using Python and uv.

**Configure VS Code**

Create a file named `mcp.json` in the `.vscode` folder of your workspace with this configuration:

```json5 title="mcp.json"
{
	"servers": {
		"mimer-mcp-server": {
			"type": "stdio",
			"command": "uvx",
			"args": [
				"mimer_mcp_server"
			],
			"env": {
				"DOTENV_PATH": "/absolute/path/to/.env" // (1)!
			}
		}
	}
}
```

1. Replace `/absolute/path/to/.env` with the actual absolute path to your environment configuration file on your machine.

### Starting the Server

After saving your `.vscode/mcp.json` file, VS Code will display a **Start** button at the top of your server configuration.

![Screenshot](images/start-mcp-server.png)

1. Click the **Start** button to launch the Mimer MCP Server
2. Wait for the server to initialize (you should then see the number of tools listed)

### Using the Server with VS Code Copilot

Once your server is running, you can access its tools through Copilot:

1. Open **Copilot Chat** in VS Code
2. In the Copilot Chat box, select **Agent mode** from the dropdown menu ![Copilot Agent Mode](images/copilot-agent-mode.png)

3. Click the **Tools** button to view all available tools and ensure the tools from **Mimer MCP Server** are selected ![Mimer MCP Tools](images/mimer-mcp-tools.png)

You're now ready to interact with your Mimer database through natural language queries in Copilot! 

See the [Examples documentation](mimer-mcp-server/examples.md) how to prompt the AI agents to utilize tools from Mimer MCP Server.