import chess
from langchain.input import print_text

from chesster import utils


def _check_indentation(multi_line_string: str) -> None:
    """Check lines are not indented."""
    for line in multi_line_string.splitlines():
        if len(line) > 0:
            assert not line.strip("\n")[0].isspace()


def test_system_message():
    board = chess.Board()
    player_side = chess.WHITE
    system_message = utils.make_system_message(board, player_side)
    _check_indentation(system_message)
    print_text(f"\n{system_message}")
    move = chess.Move.from_uci("e2e4")
    board.push(move)
    system_message = utils.make_system_message(board, player_side)
    _check_indentation(system_message)
    print_text(f"\n------\nf{system_message}")
    move = chess.Move.from_uci("e7e5")
    board.push(move)
    system_message = utils.make_system_message(board, player_side)
    _check_indentation(system_message)
    print_text(f"\n------\nf{system_message}")
