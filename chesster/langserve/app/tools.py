import os
import requests
import urllib

from langchain.tools import StructuredTool, Tool
from langchain_core.pydantic_v1 import BaseModel, Field


def _get_server_url():
    """Get URL for app server."""
    server_host = os.getenv("SERVER_HOST", "localhost")
    server_port = os.getenv("SERVER_PORT", "8000")
    return f"http://{server_host}:{server_port}"


SERVER_URL = _get_server_url()


class InitializeGameInput(BaseModel):
    player_side: str = Field(
        ...,
        description="The player's side of choice, either 'black' or 'white'",
    )


class ChessMoveInput(BaseModel):
    move: str = Field(
        ...,
        description="The UCI string of the move, e.g., 'd2d4'",
    )


class InitializeGameFromPGNInput(BaseModel):
    pgn_string: str = Field(
        ...,
        description="The PGN string of the game, e.g., '1. d4 Nf6 2. Nc3 g6'",
    )
    player_side_string: str = Field(
        ...,
        description="The player's side of choice, either 'black' or 'white'",
    )


def _initialize_game(player_side: str) -> dict:
    """Use this tool to make a chess move. Input the move in UCI format."""
    # response = requests.post(f"{SERVER_URL}/initialize_game_vs_opponent/{player_side}")
    # return response.json()
    if "w" in player_side:
        return {"message": "Game initialized. Your move."}
    else:
        return {"message": "Game initialized. Opponent move: e4."}


def _make_chess_move(move_uci: str) -> dict:
    """Use this tool to make a chess move. Input the move in UCI format."""
    # response = requests.post(f"{SERVER_URL}/make_move_vs_opponent/{move_uci}")
    # return response.json()
    return {"message": f"Move to {move_uci} was successful."}


def _initialize_game_from_pgn(
    pgn_string: str = "", player_side_string: str = "white"
) -> dict:
    """Use this tool to initialize a previously played game."""
    # encoded_pgn_str = urllib.parse.quote(pgn_string)
    # response = requests.post(
    #     f"{SERVER_URL}/make_board_from_pgn/{encoded_pgn_str}/{player_side_string}"
    # )
    # return response.json()
    return {"message": "Successfully uploaded board"}


def _get_next_interesting_move() -> dict:
    """Use this tool to get the next interesting move according to the engine."""
    # response = requests.post(f"{SERVER_URL}/get_next_interesting_move")

    # return response.json()
    return {"message": "ok"}


def get_tools() -> list[Tool]:
    """Get tools given a board."""
    initialize_game_tool = Tool.from_function(
        func=_initialize_game,
        name="initialize_game",
        description="Use this tool to initialize a new chess game.",
        args_schema=InitializeGameInput,
    )
    chess_move_tool = Tool.from_function(
        func=_make_chess_move,
        name="make_chess_move",
        description="Use this tool to make a chess move. Input the move in UCI format.",
        args_schema=ChessMoveInput,
    )
    initialize_game_from_pgn_tool = StructuredTool.from_function(
        func=_initialize_game_from_pgn,
        name="initialize_game_from_pgn",
        description="Use this tool to initialize a game from a PGN string. Input the string as provided.",
        args_schema=InitializeGameFromPGNInput,
    )
    next_interesting_move_tool = StructuredTool.from_function(
        func=_get_next_interesting_move,
        name="get_next_interesting_move",
        description="Use this tool to identify the next interesting move.",
    )

    return [
        initialize_game_tool,
        chess_move_tool,
        initialize_game_from_pgn_tool,
        next_interesting_move_tool,
    ]
