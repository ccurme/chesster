import time
import urllib

import chess
import chess.svg
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from typing import List

from chesster.utils import display_board, get_engine_move, parse_chess_move

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


    async def set_board(self, board: chess.Board) -> None:
        """Set board."""
        self.board = board
        await self.update_board(self.board)


    async def set_player_side(self, player_side: chess.Color) -> None:
        """Set player side."""
        self.player_side = player_side
        await self.update_board(self.board)


    async def make_move(self, move: chess.Move) -> None:
        """Parse move and update board."""
        self.board.push(move)
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
async def set_player_side(color: str) -> dict:
    """Set side to black or white."""
    if "w" in color:
        player_side = chess.WHITE
        side_str = "white"
    else:
        player_side = chess.BLACK
        side_str = "black"
    await board_manager.set_player_side(player_side)
    return {"message": f"Updated player side successfully to {side_str}."}


@app.get("/initialize_game_vs_opponent/{player_side_str}")
async def initialize_game_vs_opponent(player_side_str: str) -> dict:
    await board_manager.set_board(chess.Board())
    _ = await set_player_side(player_side_str)
    if board_manager.player_side == chess.BLACK:
        opponent_move = get_engine_move(board_manager.board)
        await board_manager.make_move(opponent_move)

    return {"message": "Game initialized."}


@app.get("/make_move_vs_opponent/{move_str}")
async def make_move_vs_opponent(move_str: str) -> dict:
    """Push move to board against engine. Move should be a valid UCI string."""
    if board_manager.board.is_game_over():
        return {"message": "Game over."}
    move = parse_chess_move(board_manager.board, move_str)
    move_san = board_manager.board.san(move)
    await board_manager.make_move(move)
    opponent_move = get_engine_move(board_manager.board)
    opponent_move_san = board_manager.board.san(opponent_move)
    time.sleep(1)
    await board_manager.make_move(opponent_move)
    response = (
        f"Successfully made move to {move_san}. Opponent responded by moving"
        f" to {opponent_move_san}."
    )
    return {"message": response}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    return await board_manager.websocket_endpoint(websocket)
