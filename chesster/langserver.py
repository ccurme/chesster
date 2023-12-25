#!/usr/bin/env python
from fastapi import FastAPI
from langchain.agents import AgentExecutor
from langchain.pydantic_v1 import BaseModel, Field
from langserve import add_routes

from agent import get_agent, get_tools


app = FastAPI(
  title="Chesster chat server.",
  version="1.0",
)

class AgentInput(BaseModel):
    user_message: str
    chat_history: list[tuple[str, str]] = Field(
        ..., extra={"widget": {"type": "chat", "input": "input", "output": "output"}}
    )

tools = get_tools()
agent = get_agent()
agent_executor = AgentExecutor(agent=agent, tools=tools).with_types(input_type=AgentInput)

add_routes(
    app,
    agent_executor,
    path="/chesster",
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8080)
