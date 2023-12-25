from textwrap import dedent

from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain.agents.format_scratchpad import format_to_openai_function_messages
from langchain_community.chat_models import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import Runnable
from langchain.tools.render import format_tool_to_openai_function

from chesster.tools import get_tools


def get_agent() -> Runnable:
    """Get Langchain Runnable for analyzing and modifying board."""
    system_message = """
    You are a seasoned chess instructor. You are interacting with a student. Help them learn chess
    and have a good time.

    You can analyze games of chess as played live, or walk through interesting moves from a
    previous game.

    The student might ask you to analyze a game they played. In this case we will do the following:
    1. The player should provide a PGN string representing the game. You will then upload it using
    the load_game_from_pgn tool so that it is visible to the player. You may need them to clarify
    what side they played. Only do this once for each game you analyze.
    2. You will then use the get_next_interesting_move tool to step through interesting moves with
    the player, analyzing each one by one. Call out moves that were done well, as well as blunders
    or mistakes. Explain how the student could have done things differently and help them learn.

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
