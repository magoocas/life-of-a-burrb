# AGENTS.md

## Project: Life of a Burrb

This is a pygame game built collaboratively between a 10-year-old kid and Claude Code (claude-opus-4-6). The kid designs and directs; Claude handles all programming.

## Key Rules

- **Git discipline**: Commit after every meaningful change with clear, descriptive messages. The git history should tell the full story of how this game was built.
- **Single file**: The entire game lives in `game.py`. All edits are surgical (find-and-replace), never full rewrites.
- **Kid-friendly**: The player is 10 and knows nothing about programming. Explain things simply when talking to them. Never ask them to write code.
- **Dad reviews**: A parent oversees the project. Keep the git history clean and informative so he can follow along.

## Tech Stack

- Python 3.14, pygame-ce 2.5.6
- Virtual environment in `.venv/` (managed with `uv`)
- Run: `source .venv/bin/activate && python3 game.py`
- Screen: 900x700, 60 FPS
