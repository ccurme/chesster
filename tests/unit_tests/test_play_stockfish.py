from unittest.mock import MagicMock, patch
from typing import Callable

from langchain_core.runnables import Runnable

from chesster import chain


def _make_mock_llm(*args, **kwargs) -> Runnable:
    """Make mock llm for testing."""
    llm = MagicMock(spec=Runnable)
    llm.invoke.return_value = "Mock LLM response."

    return llm

@patch("chesster.chain.ChatOpenAI", return_value=_make_mock_llm)
def test_play_stockfish(mock_llm: Callable):
    # mock_llm.return_value = _make_mock_llm
    analysis_chain = chain.get_analysis_chain()
    _ = analysis_chain.invoke({
        "board_context": "test",
        "user_message": "test",
        "chat_history": [],
    })
