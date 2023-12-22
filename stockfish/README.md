# Stockfish chess engine

[Stockfish](https://stockfishchess.org/) is a high performing free and open source chess engine.
Here we provide a convenience script for downloading the engine binary for 64 bit x86 processors.

Run `stockfish/download.sh` from the project root to download the binary to the `stockfish/` folder.
By default, Chesster will search for the binary in this folder. You can override the engine location
by setting the `STOCKFISH_ENGINE_PATH` environment variable.
