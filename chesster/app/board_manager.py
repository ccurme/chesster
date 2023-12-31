import os
from typing import Iterator
import urllib

import chess
from fastapi import WebSocket, WebSocketDisconnect
from langserve import RemoteRunnable

from chesster.app.utils import (
    display_board,
    get_engine_score,
    serialize_board_state_with_last_move,
)


LANGSERVE_HOST = os.getenv("LANGSERVE_HOST", "localhost")
LANGSERVE_SECRET = os.getenv("LANGSERVE_SECRET", "secret")
CHAT_HISTORY_LENGTH = 50  # Number of most recent (human, ai) exchanges to retain.


class BoardManager:
    def __init__(self):
        self.active_websockets: list[WebSocket] = []
        self.last_updated_image = None
        self.board = chess.Board()
        self.player_side = chess.WHITE
        self.interesting_move_iterator = None
        self.chat_history = []
        self.remote_runnable = RemoteRunnable(
            f"http://{LANGSERVE_HOST}:8001/chesster", headers={"x-token": LANGSERVE_SECRET}
        )

    async def set_board(self, board: chess.Board) -> None:
        """Set board."""
        self.board = board
        await self.update_board(self.board)

    async def set_player_side(self, player_side: chess.Color) -> None:
        """Set player side."""
        self.player_side = player_side
        await self.update_board(self.board)

    async def set_interesting_move_iterator(self) -> None:
        """Calculate interesting moves in board's move stack."""
        self.interesting_move_iterator = self._interesting_move_iterator()

    async def make_move(self, move: chess.Move) -> None:
        """Parse move and update board."""
        self.board.push(move)
        await self.update_board(self.board)

    async def _interesting_move_iterator(
        self, centipawn_threshold: int = 100
    ) -> Iterator[chess.Board]:
        """Make iterator over interesting moves according to Chess engine."""
        new_board = chess.Board()
        centipawns = 0
        for move in self.board.move_stack:
            new_board.push(move)
            new_centipawns = get_engine_score(new_board, self.player_side)
            if new_centipawns is None:
                continue
            delta = new_centipawns - centipawns
            if new_board.turn != self.player_side:  # player just moved
                if abs(delta) > centipawn_threshold:
                    await self.update_board(new_board)
                    yield {
                        "board": serialize_board_state_with_last_move(
                            new_board, self.player_side
                        ),
                        "last_move_centipawns": delta,
                    }
            centipawns = new_centipawns

    async def update_board(self, board: chess.Board) -> None:
        """Update SVG string."""
        board_svg = urllib.parse.quote(str(display_board(board, self.player_side)))
        svg_string = f"data:image/svg+xml,{board_svg}"
        self.last_updated_image = svg_string
        for websocket in self.active_websockets:
            await websocket.send_text(self.last_updated_image)

    async def websocket_endpoint(self, websocket: WebSocket):
        await websocket.accept()
        self.active_websockets.append(websocket)
        try:
            welcome_message = "Welcome to Chesster!"
            await websocket.send_text(welcome_message)
            while True:
                data = await websocket.receive_text()
                if data == "Show me the image":
                    if self.last_updated_image is not None:
                        await websocket.send_text(self.last_updated_image)
                else:
                    user_message = data
                    await websocket.send_text(user_message)
                    response_message = await self.remote_runnable.ainvoke(
                        {
                            "user_message": user_message,
                            "chat_history": self.chat_history,
                        }
                    )
                    self.chat_history.append((user_message, response_message))
                    self.chat_history = self.chat_history[-CHAT_HISTORY_LENGTH:]
                    await websocket.send_text(response_message)
        except WebSocketDisconnect:
            self.active_websockets.remove(websocket)
