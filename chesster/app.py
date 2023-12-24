import urllib

import chess
import chess.svg
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from typing import List

from chesster.utils import display_board

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

class BoardManager:
    def __init__(self):
        self.active_websockets: List[WebSocket] = []
        self.last_updated_image = None
        self.board = chess.Board()
        self.player_side = chess.WHITE


    async def set_player_side(self, player_side: chess.Color) -> None:
        """Set player side."""
        self.player_side = player_side
        await self.update_board(self.board)


    async def update_board(self, board: chess.Board) -> None:
        """Update SVG string."""
        board_svg = urllib.parse.quote(str(display_board(board, self.player_side)))
        svg_string = f"data:image/svg+xml,{board_svg}"
        self.last_updated_image = svg_string
        for websocket in self.active_websockets:
            await websocket.send_text(self.last_updated_image)


    async def websocket_endpoint(self, websocket: WebSocket):
        await websocket.accept()
        self.active_websockets.append(websocket)
        try:
            while True:
                await self.update_board(self.board)
                data = await websocket.receive_text()
                if data == "Show me the image" and self.last_updated_image is not None:
                    await websocket.send_text(self.last_updated_image)
        except WebSocketDisconnect:
            self.active_websockets.remove(websocket)


board_manager = BoardManager()

@app.get("/")
async def get():
    return HTMLResponse(html)


@app.get("/set_player_side/{color}")
async def set_player_side(color: str):
    if "w" in color:
        player_side = chess.WHITE
        side_str = "white"
    else:
        player_side = chess.BLACK
        side_str = "black"
    await board_manager.set_player_side(player_side)
    return {"message": f"Updated player side successfully to {side_str}."}


@app.get("/update_image/{color}")
async def update_image(color: int):
    await board_manager.update_image(color)
    return {"message": "Image updated successfully", "color": color}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    return await board_manager.websocket_endpoint(websocket)
