import os

import chess
import chess.engine
from IPython.display import clear_output, display
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from chesster.chain import get_analysis_chain
from chesster.utils import serialize_board_state


def _get_stockfish_engine(skill_level: int = 3) -> chess.engine.SimpleEngine:
    """Load Stockfish engine."""
    engine_path = os.getenv("STOCKFISH_ENGINE_PATH", "stockfish/stockfish-ubuntu-x86-64-modern")
    engine = chess.engine.SimpleEngine.popen_uci(engine_path)
    engine.configure({"Skill Level": skill_level})

    return engine


def _get_user_move(board: chess.Board) -> chess.Move:
    """Get move from user input."""
    user_move_uci = input()

    user_move = chess.Move.from_uci(user_move_uci)
    if not board.is_legal(user_move):
        display("Illegal move, try again.")
        user_move_uci = input()
        user_move = chess.Move.from_uci(user_move_uci)
    
    return user_move


def main():

    board = chess.Board()
    chain = get_analysis_chain()
    chat_history = []

    while not board.is_game_over():
        display(board)
        user_move = _get_user_move(board)
        user_move_san = board.san(user_move)
        board.push(user_move)

        clear_output()
        display(board)
        display(user_move_san)

        engine = _get_stockfish_engine()
        engine_result = engine.play(board, chess.engine.Limit(time=0.1))
        context = SystemMessage(content=f"""Current board state:
    {serialize_board_state(board)}

    Player last move:
    {user_move_san}

    """)
        user_message = f"I just played {user_move_san}. How's that look?"

        commentary = chain.invoke({"board_context": context, "user_message": user_message, "chat_history": chat_history})
        chat_history.extend(
            [
                HumanMessage(content=user_message),
                AIMessage(content=commentary),
            ]
        )
        board.push(engine_result.move)
        clear_output()
        display(commentary)
