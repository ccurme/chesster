import urllib

import chess
from fastapi.testclient import TestClient
import pytest

from chesster.app import app


client = TestClient(app.app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "request" in response.context


def test_set_player_side():
    response = client.post("/set_player_side/w")
    assert response.status_code == 200
    assert {"message": "Updated player side successfully to white."} == response.json()

    response = client.post("/set_player_side/b")
    assert response.status_code == 200
    assert {"message": "Updated player side successfully to black."} == response.json()


def test_initialize_game_vs_opponent():
    response = client.post("/initialize_game_vs_opponent/w")
    assert response.status_code == 200
    assert response.json() == {"message": "Game initialized. Your move."}
    assert [] == app.board_manager.board.move_stack

    response = client.post("/initialize_game_vs_opponent/b")
    assert response.status_code == 200
    assert "Opponent move" in response.json()["message"]
    assert 1 == len(app.board_manager.board.move_stack)


def test_make_move_vs_opponent():
    _ = client.post("/initialize_game_vs_opponent/w")
    with pytest.raises(chess.IllegalMoveError):
        _ = client.post("/make_move_vs_opponent/e5")
    response = client.post("/make_move_vs_opponent/e2e4")
    assert response.status_code == 200
    assert 2 == len(app.board_manager.board.move_stack)
    first_move = app.board_manager.board.move_stack[0]
    assert chess.Move.from_uci("e2e4") == first_move


def test_make_board_from_pgn_and_get_interesting_moves():
    pgn = "d4 Nf6 2. Nc3 g6 3. Bf4 Bg7 4. Nb5 d6"
    encoded_pgn = urllib.parse.quote(pgn)
    response = client.post(f"/make_board_from_pgn/{encoded_pgn}/w")
    assert response.status_code == 200
    assert [
        chess.Move.from_uci("d2d4"),
        chess.Move.from_uci("g8f6"),
        chess.Move.from_uci("b1c3"),
        chess.Move.from_uci("g7g6"),
        chess.Move.from_uci("c1f4"),
        chess.Move.from_uci("f8g7"),
        chess.Move.from_uci("c3b5"),
        chess.Move.from_uci("d7d6"),
    ] == app.board_manager.board.move_stack

    response = client.post("/get_next_interesting_move")
    assert response.status_code == 200
    response_data = response.json()
    assert {"board", "last_move_centipawns"} == set(response_data["result"].keys())
