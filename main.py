import asyncio
import os

from bot import main


async def health_server():
    port = int(os.getenv("PORT", "10000"))

    async def handle(reader, writer):
        try:
            await reader.read(4096)

            response = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: text/plain; charset=utf-8\r\n"
                "Content-Length: 25\r\n"
                "Connection: close\r\n"
                "\r\n"
                "Tepthon Factory is running"
            )

            writer.write(response.encode())
            await writer.drain()
        except Exception:
            pass
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass

    server = await asyncio.start_server(
        handle,
        "0.0.0.0",
        port,
    )

    print(f"HTTP server running on 0.0.0.0:{port}")

    return server


async def run():
    server = await health_server()

    try:
        await main()
    finally:
        server.close()
        await server.wait_closed()


if __name__ == "__main__":
    asyncio.run(run())
