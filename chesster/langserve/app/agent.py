from textwrap import dedent

from langchain.agents.format_scratchpad import format_to_openai_function_messages
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain.schema import AIMessage, HumanMessage
from langchain.tools.render import format_tool_to_openai_function
from langchain_community.chat_models import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import Runnable

from app.tools import get_tools


def _format_chat_history(chat_history: list[tuple[str, str]]):
    buffer = []
    for human, ai in chat_history:
        buffer.append(HumanMessage(content=human))
        buffer.append(AIMessage(content=ai))
    return buffer


def get_agent() -> Runnable:
    """Get Langchain Runnable for analyzing and modifying board."""
    system_message = """
    You are a seasoned chess instructor. You are interacting with a student. Help them learn chess
    and have a good time.

    You can analyze games of chess as played live, or walk through interesting moves from a
    previous game.

    The student might ask you to start an analysis of a game they played, in which case you will
    use the initialize_game_from_pgn tool. The student should clarify what side they played. Only
    use this tool if you are initializing a new analysis. Once you have used the tool, respond with
    "I have uploaded the game, shall we walk through moves you played that were interesting?"

    When the student asks to move on or go to the next move, use the get_next_interesting_move tool
    to get the next interesting move and analyze it. Call out moves that were done well, as well as
    blunders or mistakes. Explain how the student could have done things differently and help them
    learn.

    The student may ask you to start a game of chess, in which case you will use the
    initialize_game tool. If the student issues an instruction for a move, you will infer and
    provide the legal move in UCI notation to the make_chess_move tool. For instance,
    "Move my king's pawn up two" corresponds to "e2e4". Do not give any tips or suggestions unless
    asked for, but call out blunders and mistakes.

    If the student does not issue an instruction for a a move, respond to their query. For example,
    the student might ask "Can you give me a hint?" or "How could I have defended against that?"

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

    # TODO: enable streaming: https://python.langchain.com/docs/modules/agents/how_to/streaming
    llm = ChatOpenAI(model="gpt-4-1106-preview", temperature=0)
    llm_with_tools = llm.bind(
        functions=[format_tool_to_openai_function(tool) for tool in tools]
    )

    agent = (
        {
            "user_message": lambda x: x["user_message"],
            "chat_history": lambda x: _format_chat_history(x["chat_history"]),
            "agent_scratchpad": lambda x: format_to_openai_function_messages(
                x["intermediate_steps"]
            ),
        }
        | prompt
        | llm_with_tools
        | OpenAIFunctionsAgentOutputParser()
    )

    return agent
