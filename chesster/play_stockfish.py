import json
import os
import time

import chess
import chess.engine
from IPython.display import clear_output, display
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from chesster.chain import get_analysis_chain
from chesster.utils import display_board, make_system_message


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
    engine.quit()
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


def main() -> chess.Board:
    """Gameplay loop."""
    board.player_side = _get_player_side()

    board = chess.Board()
    chain = get_analysis_chain()
    chat_history = []

    if board.player_side == chess.BLACK:
        engine_move = _get_engine_move(board)
        board.push(engine_move)

    while not board.is_game_over():
        display_board(board)
        user_message = input()
        context = SystemMessage(content=make_system_message(board))
        response_str = chain.invoke(
            {
                "board_context": context,
                "user_message": user_message,
                "chat_history": chat_history,
            }
        )
        response = json.loads(response_str)
        commentary = response["commentary"]
        chat_history.extend(
            [
                HumanMessage(content=user_message),
                AIMessage(content=commentary),
            ]
        )
        user_move_uci = response["move"]
        if user_move_uci:
            try:
                user_move = chess.Move.from_uci(user_move_uci)
            except chess.InvalidMoveError:
                user_move = board.parse_san(user_move_uci)  # LLM sometimes outputs SAN
            board.push(user_move)

            clear_output()
            display_board(board)

            engine_move = _get_engine_move(board)
            time.sleep(0.5)
            board.push(engine_move)
        clear_output()
        display(commentary)

    return board
