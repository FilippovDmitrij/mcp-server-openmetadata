#src/main.py

from typing import Any, Dict, List

import click
from mcp.server import Server
from mcp.types import Resource, TextContent, Tool

from src.config import Config
from src.mcp_components.resources import list_all_resources
from src.mcp_components.tools import call_tool, list_all_tools
from src.openmetadata import OpenMetadataClient
from src.server import get_server_runner

DEFAULT_PORT = 8000
DEFAULT_TRANSPORT = "sse"
SERVER_NAME = "mcp-server-openmetadata"


@click.command()
@click.option("--port", default=DEFAULT_PORT, help="Port to listen on for SSE")
@click.option("--transport", default=DEFAULT_TRANSPORT, type=click.Choice(["stdio", "sse"]))
def main(port: int, transport: str) -> int:
    # Get OpenMetadata credentials from environment
    config = Config.from_env()

    # Initialize OpenMetadata client
    client = OpenMetadataClient(
        host=config.OPENMETADATA_HOST,
        api_token=config.OPENMETADATA_JWT_TOKEN,
        username=config.OPENMETADATA_USERNAME,
        password=config.OPENMETADATA_PASSWORD,
    )

    # Create MCP server
    app = Server(SERVER_NAME)

    """@app.list_resources()
    async def handle_list_resources() -> List[Resource]:
        return list_all_resources()"""

    @app.list_tools()
    async def handle_list_tools() -> List[Tool]:
        return list_all_tools()

    @app.call_tool()
    async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        return call_tool(name, arguments, client)

    # Start server
    try:
        server_runner = get_server_runner(app, transport, port=port)
        return server_runner()
    except Exception as e:
        print(f"Server failed to start: {str(e)}")
        return 1


if __name__ == "__main__":
    main()
