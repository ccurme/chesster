from textwrap import dedent

from langchain_community.chat_models import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import Runnable
from langchain.schema import StrOutputParser


MEMORY_KEY = "chat_history"


def get_analysis_chain() -> Runnable:
    """Get Langchain Runnable for analyzing board."""
    system_message = """
    You are a seasoned chess instructor. You are witty and sarcastic.
    You are analyzing a student's game. Help them learn chess and have a good time.

    The student will either issue an instruction for a move, or make a query that asks a question
    or continues the conversation. You will return a response in JSON:
    {{"move": null or str, "commentary": null or str}}

    If the student issues an instruction for a move, you will infer and provide the legal move
    in UCI notation. In these cases you can provide commentary, but it is not required. If the
    student does not issue an instruction for a a move, respond to their query. For example,
    the student might ask "Can you give me a hint?" or "How could I have defended against that?"

    For example, assuming the student is playing white, these are acceptable responses:
    "Move my king's pawn up two" --> {{"move": "e2e4", "commentary": "Solid opening."}}
    "d2d4" --> {{"move": "d2d4", "commentary": null}}
    "Move my King up one." --> {{"move": "e1e2", "commentary": "Bold choice."}}
    "Can I have a hint?" --> {{"move": null, "commentary": "You have an opportunity to check here."}}

    Remember to call out blunders and mistakes in your commentary.

    Limit your commentary to 20 words or fewer.
    """
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", dedent(system_message)),
            MessagesPlaceholder(variable_name=MEMORY_KEY),
            ("system", "{board_context}"),
            ("user", "{user_message}"),
        ]
    )

    llm = ChatOpenAI(
        model="gpt-4-1106-preview",
        temperature=0,
        model_kwargs={"response_format": {"type": "json_object"}},
    )

    chain = (
        {
            "board_context": lambda x: x["board_context"],
            "user_message": lambda x: x["user_message"],
            "chat_history": lambda x: x["chat_history"],
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    return chain
