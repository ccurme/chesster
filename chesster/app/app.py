import time
from typing import Any, AsyncIterator

import chess
import chess.svg
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from chesster.app.board_manager import BoardManager
from chesster.app.utils import (
    get_engine_move,
    parse_chess_move,
    parse_pgn_into_move_list,
    serialize_board_state,
    serialize_board_state_with_last_move,
)


app = FastAPI()
app.mount("/static", StaticFiles(directory="chesster/app/static"), name="static")
templates = Jinja2Templates(directory="chesster/app/templates")

board_manager = BoardManager()
CHAT_HISTORY_LENGTH = 50  # Number of most recent (human, ai) exchanges to retain.


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.post("/set_player_side/{color}")
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


@app.post("/initialize_game_vs_opponent/{player_side_str}")
async def initialize_game_vs_opponent(player_side_str: str) -> dict:
    """Start new game."""
    await board_manager.set_board(chess.Board())
    _ = await set_player_side(player_side_str)
    if board_manager.player_side == chess.BLACK:
        opponent_move = get_engine_move(board_manager.board)
        opponent_move_san = board_manager.board.san(opponent_move)
        await board_manager.make_move(opponent_move)
        response = f"Game initialized. Opponent move: {opponent_move_san}."
    else:
        response = "Game initialized. Your move."

    return {"message": response}


@app.post("/make_move_vs_opponent/{move_str}")
async def make_move_vs_opponent(move_str: str) -> dict:
    """Push move to board against engine. Move should be a valid UCI string."""
    if board_manager.board.is_game_over():
        return {"message": "Game over."}
    move = parse_chess_move(board_manager.board, move_str)
    if not board_manager.board.is_legal(move):
        return {"message": "Illegal move, try again."}
    move_san = board_manager.board.san(move)
    await board_manager.make_move(move)
    opponent_move = get_engine_move(board_manager.board)
    opponent_move_san = board_manager.board.san(opponent_move)
    time.sleep(1)
    await board_manager.make_move(opponent_move)
    response = (
        f"Successfully made move to {move_san}. Opponent responded by moving"
        f" to {opponent_move_san}.\n\n"
        f"Board state:\n{serialize_board_state(board_manager.board, board_manager.player_side)}"
    )
    return {"message": response}


@app.post("/make_board_from_pgn/{pgn_str}/{player_side_str}")
async def make_board_from_pgn(pgn_str: str, player_side_str: str) -> dict:
    """Initialize board from PGN string."""
    move_stack = parse_pgn_into_move_list(pgn_str)
    await board_manager.set_board(chess.Board())
    _ = await set_player_side(player_side_str)
    for move in move_stack:
        await board_manager.make_move(move)
    await board_manager.set_interesting_move_iterator()
    response = (
        "Successfully uploaded board. Board state:\n"
        f"{serialize_board_state(board_manager.board, board_manager.player_side)}"
    )
    return {"message": response}


async def _safe_next(iterator: AsyncIterator) -> Any:
    """Next but catch StopIteration and return a message."""
    try:
        return await anext(iterator)
    except StopAsyncIteration:
        return {"result": "End of iteration."}


@app.post("/get_next_interesting_move/")
async def get_next_interesting_move() -> dict:
    result = await _safe_next(board_manager.interesting_move_iterator)
    await board_manager.display_board(result["board"], board_manager.active_websockets)
    result["board"] = serialize_board_state_with_last_move(result["board"], board_manager.player_side)
    return {"result": result}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    board_manager.active_websockets.append(websocket)
    try:
        welcome_message = "Welcome to Chesster!"
        await websocket.send_text(welcome_message)
        while True:
            data = await websocket.receive_text()
            if data == "Show me the image":
                if board_manager.last_updated_image is not None:
                    await websocket.send_text(board_manager.last_updated_image)
            else:
                user_message = data
                await websocket.send_text(user_message)
                response_message = await board_manager.remote_runnable.ainvoke(
                    {
                        "user_message": user_message,
                        "chat_history": board_manager.chat_history,
                    }
                )
                board_manager.chat_history.append((user_message, response_message))
                board_manager.chat_history = board_manager.chat_history[-CHAT_HISTORY_LENGTH:]
                await websocket.send_text(response_message)
    except WebSocketDisconnect:
        board_manager.active_websockets.remove(websocket)
