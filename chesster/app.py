from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from typing import List

app = FastAPI()

active_websockets: List[WebSocket] = []

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

@app.get("/")
async def get():
    return HTMLResponse(html)

red_square_svg = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 50 50'%3E%3Crect width='50' height='50' style='fill:rgb(255,0,0);stroke-width:0;stroke:rgb(0,0,0)' /%3E%3C/svg%3E"
blue_square_svg = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 50 50'%3E%3Crect width='50' height='50' style='fill:rgb(0,0,255);stroke-width:0;stroke:rgb(0,0,0)' /%3E%3C/svg%3E"
global_images = [red_square_svg, blue_square_svg]

last_updated_image = None

@app.get("/update_image/{color}")
async def update_image(color: int):
    global last_updated_image
    if color == 1:
        last_updated_image = global_images[0]
    else:
        last_updated_image = global_images[1]

    for websocket in active_websockets:
        await websocket.send_text(last_updated_image)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_websockets.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "Show me the image" and last_updated_image is not None:
                await websocket.send_text(last_updated_image)
    except WebSocketDisconnect:
        active_websockets.remove(websocket)
