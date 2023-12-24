from textwrap import dedent
from typing import Any, Iterator

import chess
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain.agents.format_scratchpad import format_to_openai_function_messages
from langchain_community.chat_models import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import Runnable
from langchain.tools import Tool
from langchain.tools.render import format_tool_to_openai_function

from chesster.utils import display_board, get_stockfish_engine, make_system_message


def _interesting_move_iterator(
    board: chess.Board, centipawn_threshold : int = 100,
) -> Iterator[chess.Board]:
    """Make iterator over interesting moves according to Chess engine."""
    engine = get_stockfish_engine()
    new_board = chess.Board()
    new_board.player_side = board.player_side
    for move in board.move_stack:
        new_board.push(move)
        if new_board.turn != board.player_side:  # player just moved
            analysis = engine.analyse(new_board, chess.engine.Limit(time=0.1))
            score = analysis["score"]
            if board.player_side == chess.WHITE:
                centipawns = score.white().score()
            else:
                centipawns = score.black().score()
            if centipawns is not None and (abs(centipawns) > centipawn_threshold):
                display_board(new_board)
                yield {"board": make_system_message(new_board), "last_move_centipawns": centipawns}


def _safe_next(iterator: Iterator) -> Any:
    """Next but catch StopIteration and return a message."""
    try:
        return next(iterator)
    except StopIteration:
        return "End of iteration."


def _get_tools(board: chess.Board | None = None) -> list[Tool]:
    """Get tools given a board."""
    # N.B. we accept None as a hack to make it easy to generate function definitions
    # without a board.
    interesting_moves = _interesting_move_iterator(board)
    next_interesting_move_tool = Tool.from_function(
        func=lambda x: _safe_next(interesting_moves),
        name="get_next_interesting_move",
        description="Use this tool to identify the next interesting move. Always pass an empty string.",
    )

    return [next_interesting_move_tool]


def get_analysis_agent() -> Runnable:
    """Get Langchain Runnable for analyzing a past game."""
    system_message = """
    You are a seasoned chess instructor. You are analyzing a student's game. Help them learn
    chess and have a good time.

    Walk through the completed game with the player, analyzing interesting moves. Call out
    moves that were done well, as well as blunders or mistakes. Explain how the student could
    have done things differently and help them learn.

    At the start of the conversation, always use the get_next_interesting_move function to get
    the first move.

    Rrespond to the student's follow up queries.

    Limit your commentary to 100 words or fewer.
    """
    tools = _get_tools()
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", dedent(system_message)),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{user_message}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )

    llm = ChatOpenAI(model="gpt-4-1106-preview", temperature=0)
    llm_with_tools = llm.bind(
        functions=[format_tool_to_openai_function(tool) for tool in tools]
    )

    agent = (
        {
            "user_message": lambda x: x["user_message"],
            "chat_history": lambda x: x["chat_history"],
            "agent_scratchpad": lambda x: format_to_openai_function_messages(
                x["intermediate_steps"]
            ),
        }
        | prompt
        | llm_with_tools
        | OpenAIFunctionsAgentOutputParser()
    )

    return agent
