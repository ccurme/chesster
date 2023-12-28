from functools import partial
from textwrap import dedent

import chess
from langchain.agents import AgentExecutor
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain.agents.format_scratchpad import format_to_openai_function_messages
from langchain_community.chat_models import ChatOpenAI
from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.runnables import Runnable
from langchain.tools import Tool
from langchain.tools.render import format_tool_to_openai_function

from chesster.utils import make_system_message


class ChessMoveInput(BaseModel):
    move: str = Field()


def _make_chess_move(board: chess.Board, move_uci: str) -> None:
    """ "Use this tool to make a chess move. Input the move in UCI format."""
    try:
        move = chess.Move.from_uci(move_uci)
    except chess.InvalidMoveError:
        move = board.parse_san(move_uci)  # LLM sometimes outputs SAN
    board.push(move)


def _get_tools(board: chess.Board | None = None) -> list[Tool]:
    """Get tools given a board."""
    # N.B. we accept None as a hack to make it easy to generate function definitions
    # without a board.
    chess_move_tool = Tool.from_function(
        func=partial(_make_chess_move, board),
        name="make_chess_move",
        description="Use this tool to make a chess move. Input the move in UCI format.",
        args_schema=ChessMoveInput,
    )

    return [chess_move_tool]


def get_analysis_agent() -> Runnable:
    """Get Langchain Runnable for analyzing and modifying board."""
    system_message = """
    You are a seasoned chess instructor. You are witty and sarcastic.
    You are analyzing a student's game. Help them learn chess and have a good time.

    The student will either issue an instruction for a move, or make a query that asks a question
    or continues the conversation.

    If the student issues an instruction for a move, you will infer and provide the legal move
    in UCI notation. For instance, "Move my king's pawn up two" corresponds to "e2e4".

    If the student does not issue an instruction for a a move, respond to their query. For example,
    the student might ask "Can you give me a hint?" or "How could I have defended against that?"

    Remember to call out blunders and mistakes in your commentary.

    Limit your commentary to 20 words or fewer.
    """
    tools = _get_tools()
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", dedent(system_message)),
            MessagesPlaceholder(variable_name="chat_history"),
            ("system", "{board_context}"),
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
            "board_context": lambda x: x["board_context"],
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


def query_agent(user_message: str, board: chess.Board, chat_history: list) -> dict:
    """Build board context and query agent."""
    agent = get_analysis_agent()
    tools = _get_tools(board)
    agent_executor = AgentExecutor(agent=agent, tools=tools)

    board_context = SystemMessage(content=make_system_message(board))

    return agent_executor.invoke(
        {
            "board_context": board_context,
            "user_message": user_message,
            "chat_history": chat_history,
        },
    )
