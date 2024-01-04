from unittest.mock import MagicMock, patch

from langchain.agents import AgentExecutor
from langchain_core.messages import AIMessage
from langchain_core.runnables import Runnable

from chesster.langserve import agent


def _make_mock_llm(*args, **kwargs) -> Runnable:
    """Make mock llm for testing."""
    llm = MagicMock(spec=Runnable)
    llm.invoke.side_effect = [
        AIMessage(
            content="",
            additional_kwargs={
                "function_call": {
                    "arguments": '{"player_side":"white"}',
                    "name": "initialize_game",
                }
            },
        ),
        AIMessage(content="OK, your move."),
        AIMessage(
            content="",
            additional_kwargs={
                "function_call": {
                    "arguments": '{"move_uci":"d2d4"}',
                    "name": "make_chess_move",
                }
            },
        ),
        AIMessage(content="Solid opening."),
        AIMessage(
            content="",
            additional_kwargs={
                "function_call": {
                    "arguments": '{"move_uci":"b1c3"}',
                    "name": "make_chess_move",
                }
            },
        ),
        AIMessage(content=""),
        AIMessage(
            content="",
            additional_kwargs={
                "function_call": {
                    "arguments": '{"player_side":"black"}',
                    "name": "initialize_game",
                }
            },
        ),
        AIMessage(content="OK, white just played e4. Your move."),
        AIMessage(content="Try to control the center."),
        AIMessage(
            content="",
            additional_kwargs={
                "function_call": {
                    "arguments": (
                        '{"pgn_string":"d4 Nf6 2. Nc3 g6 3. Bf4 Bg7 '
                        '4. Nb5 d6","player_side_string":"black"}'
                    ),
                    "name": "initialize_game_from_pgn",
                }
            },
        ),
        AIMessage(content=("I have uploaded the game, shall we walk through it?")),
        AIMessage(
            content="",
            additional_kwargs={
                "function_call": {
                    "arguments": "{}",
                    "name": "_get_next_interesting_move",
                }
            },
        ),
        AIMessage(content="This move was terrible."),
    ]
    llm.bind = lambda *args, **kwargs: llm

    return llm


@patch("requests.post")
@patch("chesster.langserve.agent.ChatOpenAI", return_value=_make_mock_llm())
def test_agent(mock_llm, mock_post):

    tools = agent.get_tools(pass_board_id=True)
    agent_runnable = agent.get_agent()
    agent_executor = AgentExecutor(agent=agent_runnable, tools=tools)
    chat_history = []

    mock_post.return_value.json.return_value = {"message": "Successfully used tool."}
    mock_post.return_value.status_code = 200

    inputs_and_responses = [
        ("let's play a game", "OK, your move."),
        ("d4", "Solid opening."),
        ("Nc3", ""),
        ("actually let me play as black", "OK, white just played e4. Your move."),
        ("what should I think about here?", "Try to control the center."),
        (
            (
                "can you analyze this game? I played white: "
                "d4 Nf6 2. Nc3 g6 3. Bf4 Bg7 4. Nb5 d6"
            ),
            "I have uploaded the game, shall we walk through it?",
        ),
        ("go ahead", "This move was terrible."),
    ]
    for user_message, expected_response in inputs_and_responses:
        response = agent_executor.invoke(
            {
                "user_message": user_message,
                "chat_history": chat_history,
                "board_id": "0",
            }
        )
        chat_history.append((user_message, response["output"]))
        assert response["output"] == expected_response


def test_add_board_id_to_function_call():
    ai_message = AIMessage(content="Let's play chess.")
    board_id = "0"
    result = agent._add_board_id_to_function_call(
        {"ai_message": ai_message, "board_id": board_id}
    )
    assert result == ai_message

    ai_message = AIMessage(
        content="",
        additional_kwargs={
            "function_call": {
                "arguments": '{"player_side":"white"}',
                "name": "initialize_game",
            }
        },
    )
    result = agent._add_board_id_to_function_call(
        {"ai_message": ai_message, "board_id": board_id}
    )
    expected = AIMessage(
        content="",
        additional_kwargs={
            "function_call": {
                "arguments": '{"player_side": "white", "board_id": "0"}',
                "name": "initialize_game",
            }
        },
    )
    assert expected == result

    ai_message = AIMessage(
        content="",
        additional_kwargs={
            "function_call": {"arguments": "{}", "name": "get_next_interesting_move"}
        },
    )
    result = agent._add_board_id_to_function_call(
        {"ai_message": ai_message, "board_id": board_id}
    )
    expected = AIMessage(
        content="",
        additional_kwargs={
            "function_call": {
                "arguments": '{"board_id": "0"}',
                "name": "get_next_interesting_move",
            }
        },
    )
    assert expected == result
