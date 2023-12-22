import os
from textwrap import dedent

import chess
import chess.engine
from IPython.display import clear_output, display
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from chesster.chain import get_analysis_chain
from chesster.utils import display_board, make_system_message


def _get_user_move(board: chess.Board) -> chess.Move:
    """Get move from user input."""
    user_move_uci = input()

    user_move = chess.Move.from_uci(user_move_uci)
    if not board.is_legal(user_move):
        display("Illegal move, try again.")
        user_move_uci = input()
        user_move = chess.Move.from_uci(user_move_uci)

    return user_move


def _get_stockfish_engine(skill_level: int = 3) -> chess.engine.SimpleEngine:
    """Load Stockfish engine."""
    engine_path = os.getenv(
        "STOCKFISH_ENGINE_PATH", "stockfish/stockfish-ubuntu-x86-64-modern"
    )
    engine = chess.engine.SimpleEngine.popen_uci(engine_path)
    engine.configure({"Skill Level": skill_level})

    return engine


def _get_engine_move(board: chess.Board) -> chess.Move:
    """Get move from engine."""
    engine = _get_stockfish_engine()
    engine_result = engine.play(board, chess.engine.Limit(time=0.1))
    return engine_result.move


def _get_player_side():
    """Get side for user at game start."""
    display("User plays as black or white?")
    player_side_str = input()
    clear_output()
    if "w" in player_side_str.lower():
        return chess.WHITE
    else:
        return chess.BLACK


def main():
    """Gameplay loop."""
    player_side = _get_player_side()

    board = chess.Board()
    chain = get_analysis_chain()
    chat_history = []

    if player_side == chess.BLACK:
        engine_move = _get_engine_move(board)
        board.push(engine_move)

    while not board.is_game_over():
        display_board(board, player_side=player_side)
        user_move = _get_user_move(board)
        user_move_san = board.san(user_move)
        board.push(user_move)

        clear_output()
        display_board(board, player_side=player_side)

        context = SystemMessage(content=make_system_message(board, player_side))
        user_message = f"I just played {user_move_san}. How's that look?"

        commentary = chain.invoke(
            {
                "board_context": context,
                "user_message": user_message,
                "chat_history": chat_history,
            }
        )
        chat_history.extend(
            [
                HumanMessage(content=user_message),
                AIMessage(content=commentary),
            ]
        )
        engine_move = _get_engine_move(board)
        board.push(engine_move)
        clear_output()
        display(commentary)
