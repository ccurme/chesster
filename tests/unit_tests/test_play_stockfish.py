from unittest.mock import MagicMock, patch
from typing import Callable

from langchain_core.messages import AIMessage
from langchain_core.runnables import Runnable

from chesster import play_stockfish


def _make_mock_llm(*args, **kwargs) -> Runnable:
    """Make mock llm for testing."""
    llm = MagicMock(spec=Runnable)
    llm.invoke.side_effect = [
        AIMessage(
            content="",
            additional_kwargs={
                "function_call": {
                    "arguments": '{"move":"d2d4"}',
                    "name": "make_chess_move",
                }
            },
        ),
        AIMessage(content="Solid opening."),
        AIMessage(
            content="",
            additional_kwargs={
                "function_call": {
                    "arguments": '{"move":"b1c3"}',
                    "name": "make_chess_move",
                }
            },
        ),
        AIMessage(content=""),
        AIMessage(
            content="",
            additional_kwargs={
                "function_call": {
                    "arguments": '{"move":"c1f4"}',
                    "name": "make_chess_move",
                }
            },
        ),
        AIMessage(content=""),
    ]
    llm.bind = lambda *args, **kwargs: llm

    return llm


@patch("chesster.play_stockfish.input", side_effect=["w", "d4", "Nc3", "c1f4"])
@patch(
    "chesster.play_stockfish.chess.Board.is_game_over",
    side_effect=[False, False, False, True],
)
@patch("chesster.agent.ChatOpenAI", return_value=_make_mock_llm())
def test_play_stockfish(
    mock_llm: Callable, mock_is_game_over: Callable, user_input: Callable
):
    board = play_stockfish.main()
    assert 6 == len(board.move_stack)
