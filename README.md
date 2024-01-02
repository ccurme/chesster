# ♟️ Chesster

Chesster is a conversational AI Chess teacher. Given a [PGN](https://en.wikipedia.org/wiki/Portable_Game_Notation) dump of a game or sequence of moves, Chesster will walk you through interesting moments, highlight successes and mistakes, and simulate alternate scenarios.

Chesster will also attend as you play a game against the computer (currently the [Stockfish](https://stockfishchess.org/) engine), answering questions and identifying opportunities to learn.

https://github.com/ccurme/chesster/assets/26529506/0dc44fce-14f8-4f5e-aefa-6a8cc6fb1a6a

Currently, the only mode of interaction with Chesster is via natural language conversation. Moves are made by describing them or specifying them with [algebraic](https://en.wikipedia.org/wiki/Algebraic_notation_(chess)) or [UCI](https://en.wikipedia.org/wiki/Universal_Chess_Interface) notation. Chesster will modify the board and take other actions based on your queries.

## Usage
Chesster includes an application server and a separate [Langserve](https://github.com/langchain-ai/langserve) server for LLM orchestration. They can be built and launched with
```
docker-compose build base
docker-compose build langserver app

OPENAI_API_KEY=... docker-compose up
```
Alternatively, you can run locally with
```
OPENAI_API_KEY=... make start
```
### Tests
```
make unit_tests
```
