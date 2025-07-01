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
DEFAULT_TRANSPORT = "stdio"
SERVER_NAME = "mcp-server-openmetadata"


@click.command()
@click.option("--port", default=DEFAULT_PORT, help="Port to listen on for SSE")
@click.option("--transport", default=DEFAULT_TRANSPORT, type=click.Choice(["stdio", "sse"]))
def main(port: int, transport: str) -> int:
    # Get OpenMetadata credentials from environment
    config = Config.from_env()

    # Initialize OpenMetadata client
    # Новый клиент принимает base_url и token
    client = OpenMetadataClient(
        base_url=config.OPENMETADATA_HOST, # OPENMETADATA_HOST должен быть полным URL, включая /api
        token=config.OPENMETADATA_JWT_TOKEN,
        # username и password не используются в новом клиенте, если есть токен
    )

    # Create MCP server
    app = Server(SERVER_NAME)

    @app.list_resources()
    async def handle_list_resources() -> List[Resource]:
        return list_all_resources() # Эта функция остаётся синхронной, если не требует клиента

    @app.list_tools()
    async def handle_list_tools() -> List[Tool]:
        # Эта функция также может оставаться синхронной, т.к. просто возвращает определения инструментов
        return list_all_tools()

    @app.call_tool()
    async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        # call_tool теперь должна быть async, так как методы клиента async
        # и сам call_tool будет вызывать await client.method()
        # Убедимся, что call_tool в mcp_components.tools также async
        return await call_tool(name, arguments, client)

    async def run_server():
        try:
            server_runner = get_server_runner(app, transport, port=port)
            # Если server_runner - это синхронная функция, которая блокирует,
            # а нам нужно управлять жизненным циклом клиента (например, закрыть сессию),
            # это может потребовать более сложной обвязки.
            # Однако, стандартные MCP серверы обычно не требуют явного закрытия клиента здесь,
            # так как клиент используется по запросу.
            # Важно закрыть сессию клиента при завершении работы приложения.
            server_runner() # Предполагаем, что это блокирующий вызов
            return 0
        except Exception as e:
            print(f"Server failed to start or run: {str(e)}")
            return 1
        finally:
            # Закрываем сессию клиента при завершении работы сервера
            # Это важно для aiohttp
            if client:
                await client.close_session()
                print("OpenMetadata client session closed.")

    # Запуск основного цикла событий asyncio для run_server
    # click команды по умолчанию синхронные. Чтобы запустить async код из click,
    # можно использовать asyncio.run()
    import asyncio
    return asyncio.run(run_server())


if __name__ == "__main__":
    # main() возвращает результат asyncio.run, который должен быть int
    exit_code = main()
    import sys
    sys.exit(exit_code)
