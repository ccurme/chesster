import io
import os
from typing import Any, Iterable, Iterator

import chess
import chess.engine
import chess.pgn
import chess.svg
from IPython.core.interactiveshell import InteractiveShell
from IPython.display import display


def _clean_up_prompt(prompt: str) -> str:
    """Remove leading whitespaces. Like `dedent` but does not require common indentation."""
    return "\n".join(line.lstrip() for line in prompt.splitlines())


def safe_next(iterator: Iterator) -> Any:
    """Next but catch StopIteration and return a message."""
    try:
        return anext(iterator)
    except StopIteration:
        return "End of iteration."


def get_stockfish_engine(skill_level: int = 3) -> chess.engine.SimpleEngine:
    """Load Stockfish engine."""
    engine_path = os.getenv(
        "STOCKFISH_ENGINE_PATH", "stockfish/stockfish-ubuntu-x86-64-modern"
    )
    engine = chess.engine.SimpleEngine.popen_uci(engine_path)
    engine.configure({"Skill Level": skill_level})

    return engine


def get_engine_move(board: chess.Board) -> chess.Move:
    """Get move from engine."""
    engine = get_stockfish_engine()
    engine_result = engine.play(board, chess.engine.Limit(time=0.1))
    engine.quit()
    return engine_result.move


def parse_chess_move(board: chess.Board, move_uci: str) -> chess.Move:
    """ "Use this tool to make a chess move. Input the move in UCI format."""
    try:
        return chess.Move.from_uci(move_uci)
    except chess.InvalidMoveError:
        return board.parse_san(move_uci)  # LLM sometimes outputs SAN


def parse_pgn_into_move_list(game_pgn: str) -> Iterable[chess.Move]:
    """Parse PGN into list of Move objects."""
    pgn_fp = io.StringIO(game_pgn)
    game = chess.pgn.read_game(pgn_fp)
    return game.mainline_moves()


def display_board(board, player_side: chess.Color) -> None:
    """Display board."""
    board_size = 360
    if player_side == chess.WHITE:
        flipped = False
    else:
        flipped = True
    if board.move_stack:
        last_move = board.move_stack[-1]
    else:
        last_move = None
    return chess.svg.board(board, flipped=flipped, size=board_size, lastmove=last_move)


def serialize_board_state(board: chess.Board, player_side: chess.Color) -> str:
    """Serialize board state."""
    if player_side == chess.BLACK:
        board_picture = str(board.mirror())
    else:
        board_picture = str(board)
    return f"{board_picture}\n\n{chess.Board().variation_san(board.move_stack)}"


def serialize_player_side(player_side: chess.Color) -> str:
    """Cast player side to string."""
    if player_side == chess.WHITE:
        return "white"
    else:
        return "black"


def make_system_message(board: chess.Board) -> str:
    """Make message capturing board state."""
    board_state_str = f"""
        Player is playing as {serialize_player_side(board.player_side)}.

        Current board state:
        {serialize_board_state(board)}
    """
    if board.move_stack:
        last_move = board.pop()
        last_move_san = board.san(last_move)
        board.push(last_move)
        if board.turn == board.player_side:
            last_to_move = "Opponent"
        else:
            last_to_move = "Player"
        previous_move_str = f"""{last_to_move} last move:
        {last_move_san}
        """
    else:
        previous_move_str = "No moves yet."
    return _clean_up_prompt(
        f"""
        {board_state_str}

        {previous_move_str}
        """
    ).strip()
