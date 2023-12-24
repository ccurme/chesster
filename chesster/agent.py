from textwrap import dedent

import chess
from langchain.agents import AgentExecutor
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain.agents.format_scratchpad import format_to_openai_function_messages
from langchain_community.chat_models import ChatOpenAI
from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import Runnable
from langchain.tools.render import format_tool_to_openai_function

from chesster.tools import get_tools
from chesster.utils import make_system_message


def get_agent() -> Runnable:
    """Get Langchain Runnable for analyzing and modifying board."""
    system_message = """
    You are a seasoned chess instructor. You are interacting with a student. Help them learn chess
    and have a good time.

    You can analyze games of chess as played live, or walk through interesting moves from a
    previous game.

    The student might ask you to analyze a game they played. In this case they can provide a
    PGN string representing the game. You will then upload it so that it is visible to the player.
    You may need them to clarify what side they played. Once you've uploaded the game, analyze it.

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
