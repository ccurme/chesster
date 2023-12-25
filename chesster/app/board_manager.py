from typing import Iterator
import urllib

import chess
from fastapi import WebSocket, WebSocketDisconnect

from chesster.utils import display_board, get_stockfish_engine, serialize_board_state


class BoardManager:
    def __init__(self):
        self.active_websockets: list[WebSocket] = []
        self.last_updated_image = None
        self.board = chess.Board()
        self.player_side = chess.WHITE
        self.interesting_move_iterator = None


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
            self, centipawn_threshold : int = 100
        ) -> Iterator[chess.Board]:
        """Make iterator over interesting moves according to Chess engine."""
        engine = get_stockfish_engine()
        new_board = chess.Board()
        centipawns = 0
        for move in self.board.move_stack:
            new_board.push(move)
            analysis = engine.analyse(new_board, chess.engine.Limit(time=0.1))
            score = analysis["score"]
            if self.player_side == chess.WHITE:
                new_centipawns = score.white().score()
            else:
                new_centipawns = score.black().score()
            if new_centipawns is None:
                continue
            delta = new_centipawns - centipawns
            if new_board.turn != self.player_side:  # player just moved
                if (abs(delta) > centipawn_threshold):
                    await self.update_board(new_board)
                    yield {"board": serialize_board_state(new_board, self.player_side), "last_move_centipawns": delta}
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
                if data == "Show me the image" and self.last_updated_image is not None:
                    await websocket.send_text(self.last_updated_image)
        except WebSocketDisconnect:
            self.active_websockets.remove(websocket)
