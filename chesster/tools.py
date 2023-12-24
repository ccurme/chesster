import os
import requests
import urllib

from langchain_core.pydantic_v1 import BaseModel, Field
from langchain.tools import StructuredTool, Tool


SERVER_URL = os.getenv("SERVER_URL", "http://localhost:8000")


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


class LoadGameInput(BaseModel):
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
    response = requests.get(f"{SERVER_URL}/initialize_game_vs_opponent/{player_side}")
    return response.json()


def _make_chess_move(move_uci: str) -> dict:
    """Use this tool to make a chess move. Input the move in UCI format."""
    response = requests.get(f"{SERVER_URL}/make_move_vs_opponent/{move_uci}")
    return response.json()


def _load_game_from_pgn(pgn_string: str = "", player_side_string: str = "white") -> dict:
    """Use this tool to load a previously played game."""
    encoded_pgn_str = urllib.parse.quote(pgn_string)
    response = requests.get(
        f"{SERVER_URL}/make_board_from_pgn/{encoded_pgn_str}/{player_side_string}"
    )
    return response.json()


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
    load_game_tool = StructuredTool.from_function(
        func=_load_game_from_pgn,
        name="load_game_from_pgn",
        description="Use this tool to load a game from a PGN string. Input the string as provided.",
        args_schema=LoadGameInput,
    )

    return [initialize_game_tool, chess_move_tool, load_game_tool]
