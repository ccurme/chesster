import time

import chess
import chess.svg
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse

from chesster.app.board_manager import BoardManager
from chesster.app.html import html_string
from chesster.utils import get_engine_move, parse_chess_move

app = FastAPI()


board_manager = BoardManager()


@app.get("/")
async def get():
    return HTMLResponse(html_string)


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
    """Start new game."""
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
