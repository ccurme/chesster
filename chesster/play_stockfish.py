import time

import chess
import chess.engine
from IPython.display import clear_output, display
from langchain_core.messages import AIMessage, HumanMessage

from chesster.game_agent import query_agent
from chesster.utils import display_board, get_engine_move


def _get_player_side():
    """Get side for user at game start."""
    display("User plays as black or white?")
    player_side_str = input()
    clear_output()
    if "w" in player_side_str.lower():
        return chess.WHITE
    else:
        return chess.BLACK


def main() -> chess.Board:
    """Gameplay loop."""
    board = chess.Board()
    board.player_side = _get_player_side()
    chat_history = []

    if board.player_side == chess.BLACK:
        engine_move = get_engine_move(board)
        board.push(engine_move)

    while not board.is_game_over():
        display_board(board)
        user_message = input()
        response = query_agent(user_message, board, chat_history)
        commentary = response["output"]
        chat_history.extend(
            [
                HumanMessage(content=user_message),
                AIMessage(content=commentary),
            ]
        )
        if board.turn != board.player_side:
            clear_output()
            display_board(board)

            engine_move = get_engine_move(board)
            time.sleep(0.5)
            board.push(engine_move)
        clear_output()
        display(commentary)

    return board
