import os
from typing import Iterator, Optional
import urllib

import chess
from fastapi import WebSocket
from langserve import RemoteRunnable

from chesster.app.utils import (
    display_board,
    get_engine_score,
    serialize_board_state_with_last_move,
)


LANGSERVE_HOST = os.getenv("LANGSERVE_HOST", "localhost")


class BoardManager:
    def __init__(self):
        self.active_websockets: list[WebSocket] = []
        self.last_updated_image = None
        self.board = chess.Board()
        self.player_side = chess.WHITE
        self.interesting_move_iterator = None
        self.chat_history = []
        self.remote_runnable = RemoteRunnable(f"http://{LANGSERVE_HOST}:8001/chesster")

    async def set_board(self, board: chess.Board) -> None:
        """Set board."""
        self.board = board
        await self.display_board(self.board, self.active_websockets)

    async def set_player_side(self, player_side: chess.Color) -> None:
        """Set player side."""
        self.player_side = player_side
        await self.display_board(self.board, self.active_websockets)

    async def set_interesting_move_iterator(self) -> None:
        """Calculate interesting moves in board's move stack."""
        self.interesting_move_iterator = self._interesting_move_iterator()

    async def make_move(self, move: chess.Move) -> None:
        """Parse move and update board."""
        self.board.push(move)
        await self.display_board(self.board, self.active_websockets)

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
                    yield {
                        "board": new_board,
                        "last_move_centipawns": delta,
                    }
            centipawns = new_centipawns

    async def display_board(self, board: chess.Board, websockets: WebSocket) -> None:
        """Update SVG string."""
        board_svg = urllib.parse.quote(str(display_board(board, self.player_side)))
        svg_string = f"data:image/svg+xml,{board_svg}"
        self.last_updated_image = svg_string
        for websocket in websockets:
            await websocket.send_text(self.last_updated_image)
