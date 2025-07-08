from typing import Callable

import anyio
from mcp.server.stdio import stdio_server
from starlette.applications import Starlette


def get_server_runner(app: Starlette, transport: str, **kwargs) -> Callable:
    if transport == "stdio":
        return _get_stdio_server_runner(app)
    elif transport == "sse":
        port = kwargs.pop("port")
        return _get_sse_server_runner(app, port)
    else:
        raise ValueError(f"Invalid transport: {transport}")


def _get_sse_server_runner(app: Starlette, port: int) -> Callable:
    def run():
        from mcp.server.sse import SseServerTransport
        from starlette.responses import Response
        from starlette.routing import Mount, Route

        sse = SseServerTransport("/messages/")

        async def handle_sse(request):
            async with sse.connect_sse(
                    request.scope, request.receive, request._send
            ) as streams:
                await app.run(
                    streams[0], streams[1], app.create_initialization_options()
                )
            return Response()

        starlette_app = Starlette(
            debug=True,
            routes=[
                Route("/sse", endpoint=handle_sse, methods=["GET"]),
                Mount("/messages/", app=sse.handle_post_message),
            ],
        )

        import uvicorn
        uvicorn.run(starlette_app, host="127.0.0.1", port=port)

    return run


def _get_stdio_server_runner(app: Starlette) -> Callable:
    def run():
        async def arun():
            async with stdio_server() as streams:
                await app.run(streams[0], streams[1], app.create_initialization_options())

        anyio.run(arun)
        return 0

    return run