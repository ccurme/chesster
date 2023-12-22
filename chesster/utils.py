import chess


def serialize_board_state(board: chess.Board) -> str:
    """Serialize board state."""

    return chess.Board().variation_san(board.move_stack)
