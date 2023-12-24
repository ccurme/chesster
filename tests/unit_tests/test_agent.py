import chess

from chesster import game_agent


def test_move_tool():
    """Test move tool."""
    board = chess.Board()
    game_agent._make_chess_move(board, "e2e4")
    assert 1 == len(board.move_stack)
    board = chess.Board()
    game_agent._make_chess_move(board, "e4")
    assert 1 == len(board.move_stack)
