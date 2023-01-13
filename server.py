import os, requests
from aiohttp import web, ClientSession

WS_FILE = os.path.join(os.path.dirname(__file__), 'index.html')
POSTS_URL = 'https://jsonplaceholder.typicode.com/posts'
POSTS_LIST = requests.get(POSTS_URL).json()


async def wshandler(request: web.Request):
    resp = web.WebSocketResponse()
    available = resp.can_prepare(request)
    if not available:
        with open(WS_FILE, "rb") as fp:
            return web.Response(body=fp.read(), content_type="text/html")

    await resp.prepare(request)

    await resp.send_str("Welcome!!!")

    try:
        print("Someone joined.")
        for ws in request.app["sockets"]:
            await ws.send_str("Someone joined")
        request.app["sockets"].append(resp)

        async for msg in resp:
            if msg.type == web.WSMsgType.TEXT:
                for ws in request.app["sockets"]:
                    if ws is not resp:
                        await ws.send_str(msg.data)
            else:
                return resp
            
        return resp

    finally:
        request.app["sockets"].remove(resp)
        print("Someone disconnected.")
        for ws in request.app["sockets"]:
            await ws.send_str("Someone disconnected.")

async def onmessage(self, data):
    for ws in self.app["sockets"]:
        for msg in POSTS_LIST:
            await ws.send_str(msg)

async def on_shutdown(app: web.Application):
    for ws in app["sockets"]:
        await ws.close() 

async def handle(request):
    return web.json_response(POSTS_LIST);

async def main():
    async with ClientSession() as session:
        async with session.get('http://localhost:8080/posts') as response:
            print(response.status)
            print(await response.json())

def init():
    app = web.Application()
    app["sockets"] = []
    app.router.add_get("/", wshandler)
    app.router.add_get("/posts", handle)
    app.on_shutdown.append(on_shutdown)

    return app

if __name__ == '__main__':
    web.run_app(init())

