#!/usr/bin/env python
import os
from typing import Optional

from fastapi import FastAPI
from langchain_core.agents import AgentActionMessageLog
from langchain.pydantic_v1 import BaseModel, Field, validator
from langchain.schema import AIMessage
from langserve import add_routes

from chesster.langserve.agent import get_agent, get_tools


HOST = os.getenv("LANGSERVE_HOST", "localhost")

app = FastAPI(
    title="Chesster chat server.",
    version="1.0",
)

IntermediateSteps = list[tuple[AgentActionMessageLog, Optional[str]]]


class AgentInput(BaseModel):
    user_message: str
    chat_history: list[tuple[str, str]] = Field(
        ..., extra={"widget": {"type": "chat", "input": "input", "output": "output"}}
    )
    intermediate_steps: IntermediateSteps = Field()

    @validator("intermediate_steps")
    def parse_intermediate_steps(intermediate_steps: list) -> IntermediateSteps:
        """Parse intermediate steps."""
        # Message log gets parsed as list of BaseMessage
        for intermediate_step in intermediate_steps:
            message_log, _ = intermediate_step
            message_log.message_log = [
                AIMessage(
                    content=message.content, additional_kwargs=message.additional_kwargs
                )
                for message in message_log.message_log
            ]

        return intermediate_steps


tools = get_tools()
agent = get_agent().with_types(input_type=AgentInput)

add_routes(
    app,
    agent,
    path="/chesster",
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=HOST, port=8001)
