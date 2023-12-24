import os
import requests
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


SERVER_URL = os.getenv("SERVER_URL", "http://localhost:8000")


class InitializeGameInput(BaseModel):
    player_side: str = Field(
        ...,
        description="The player's side of choice, either 'black' or 'white'",
    )


class ChessMoveInput(BaseModel):
    move: str = Field(
        ...,
        description="The UCI string of the move, e.g., 'd2d4'",
    )


def _initialize_game(player_side: str) -> dict:
    """Use this tool to make a chess move. Input the move in UCI format."""
    response = requests.get(f"{SERVER_URL}/initialize_game_vs_opponent/{player_side}")
    return response.json()


def _make_chess_move(move_uci: str) -> dict:
    """Use this tool to make a chess move. Input the move in UCI format."""
    response = requests.get(f"{SERVER_URL}/make_move_vs_opponent/{move_uci}")
    return response.json()


def get_tools() -> list[Tool]:
    """Get tools given a board."""
    initialize_game_tool = Tool.from_function(
        func=_initialize_game,
        name="initialize_game",
        description="Use this tool to initialize a new chess game.",
        args_schema=InitializeGameInput,
    )
    chess_move_tool = Tool.from_function(
        func=_make_chess_move,
        name="make_chess_move",
        description="Use this tool to make a chess move. Input the move in UCI format.",
        args_schema=ChessMoveInput,
    )

    return [initialize_game_tool, chess_move_tool]


def get_agent() -> Runnable:
    """Get Langchain Runnable for analyzing and modifying board."""
    system_message = """
    You are a seasoned chess instructor. You are interacting with a student. Help them learn chess
    and have a good time.

    You can analyze games of chess as played live, or walk through interesting moves from a
    previous game.

    The student may ask you to start a game of chess, in which case you will use the
    initialize_game tool. If the student issues an instruction for a move, you will infer and
    provide the legal move in UCI notation to the make_chess_move tool. For instance,
    "Move my king's pawn up two" corresponds to "e2e4".
    
    If the student does not issue an instruction for a a move, respond to their query. For example,
    the student might ask "Can you give me a hint?" or "How could I have defended against that?"

    Remember to call out blunders and mistakes in your commentary.

    Limit your commentary to 20 words or fewer.
    """
    tools = get_tools()
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


def query_agent(user_message: str, board: chess.Board, chat_history: list) -> dict:
    """Build board context and query agent."""
    agent = get_agent()
    tools = get_tools()
    agent_executor = AgentExecutor(agent=agent, tools=tools)

    board_context = SystemMessage(content=make_system_message(board))

    return agent_executor.invoke(
        {
            "board_context": board_context,
            "user_message": user_message,
            "chat_history": chat_history,
        },
    )
