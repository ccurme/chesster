from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from typing import List

app = FastAPI()

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chesster</title>
    </head>
    <body>
        <h1>Chesster</h1>
        <img id="image" src="" alt="Board will be displayed here"/>
        <ul id='messages'>
        </ul>
        <script>
            var ws = new WebSocket("ws://localhost:8000/ws");
            ws.onopen = function(event) {
                ws.send("Show me the image");
            };
            ws.onmessage = function(event) {
                var image = document.getElementById('image')
                image.src = event.data
            };
        </script>
    </body>
</html>
"""

class ImageManager:
    def __init__(self):
        self.active_websockets: List[WebSocket] = []
        self.last_updated_image = None
        self.global_images = [
            "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 50 50'%3E%3Crect width='50' height='50' style='fill:rgb(255,0,0);stroke-width:0;stroke:rgb(0,0,0)' /%3E%3C/svg%3E",
            "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 50 50'%3E%3Crect width='50' height='50' style='fill:rgb(0,0,255);stroke-width:0;stroke:rgb(0,0,0)' /%3E%3C/svg%3E"
        ]

    async def update_image(self, color: int):
        if color == 1:
            self.last_updated_image = self.global_images[0]
        else:
            self.last_updated_image = self.global_images[1]

        for websocket in self.active_websockets:
            await websocket.send_text(self.last_updated_image)

    async def websocket_endpoint(self, websocket: WebSocket):
        await websocket.accept()
        self.active_websockets.append(websocket)
        try:
            while True:
                data = await websocket.receive_text()
                if data == "Show me the image" and self.last_updated_image is not None:
                    await websocket.send_text(self.last_updated_image)
        except WebSocketDisconnect:
            self.active_websockets.remove(websocket)

manager = ImageManager()

@app.get("/")
async def get():
    return HTMLResponse(html)

@app.get("/update_image/{color}")
async def update_image(color: int):
    return await manager.update_image(color)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    return await manager.websocket_endpoint(websocket)
