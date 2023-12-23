import chess

from chesster import agent


def test_move_tool():
    """Test move tool."""
    board = chess.Board()
    agent.make_chess_move(board, "e2e4")
    assert 1 == len(board.move_stack)
    board = chess.Board()
    agent.make_chess_move(board, "e4")
    assert 1 == len(board.move_stack)
