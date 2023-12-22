from langchain_community.chat_models import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import Runnable
from langchain.schema import StrOutputParser


MEMORY_KEY = "chat_history"

def get_analysis_chain() -> Runnable:
    """Get Langchain Runnable for analyzing board."""
    system_message = """You are a seasoned chess instructor.
    You are witty and sarcastic. You are analyzing a student's game.
    Help them learn chess and have a good time.

    Remember to call out blunders and mistakes.

    Limit your commentary to 20 words or less.
    """
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_message),
            MessagesPlaceholder(variable_name=MEMORY_KEY),
            ("system", "{board_context}"),
            ("user", "{user_message}"),
        ]
    )

    llm = ChatOpenAI(model="gpt-4-1106-preview", temperature=0)

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
