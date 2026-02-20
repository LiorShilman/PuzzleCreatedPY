# PuzzleCreatedPY

A jigsaw puzzle generator and interactive puzzle game. Includes a Python desktop app (Tkinter) for generating puzzle pieces from any image, and a browser-based puzzle game with a glassmorphism UI.

![Python](https://img.shields.io/badge/Python-3.x-blue) ![HTML5](https://img.shields.io/badge/HTML5-Canvas-orange) ![License](https://img.shields.io/badge/License-MIT-green)

## Features

- **Two puzzle modes** — simple rectangular grid or classic interlocking pieces (Bezier curves)
- **Interactive browser game** — drag-and-drop pieces onto the canvas, guided snap mode, timer, piece counter
- **Desktop GUI** — Tkinter app with image preview, threading, quality slider, output directory chooser
- **Piece export** — download individual puzzle pieces as a ZIP file
- **RTL Hebrew UI** — full Hebrew interface throughout

## Quick Start

### Browser Game

Open `Puzzle.html` in any modern browser. Upload an image, pick rows/columns, and play.

### Python Desktop App

```bash
pip install Pillow numpy
python horse-puzzle.py
```

### Headless / Programmatic

```python
from jigsaw_puzzle_generator import createPuzzlePieces, create_rectangular_pieces

# Classic interlocking pieces
createPuzzlePieces("image.jpg", 4, 6, "output/")

# Simple rectangular grid
create_rectangular_pieces("image.jpg", 4, 6, "output/")
```

Output goes to `puzzle_pieces/` — individual `piece_[row]_[col].png` files plus outline previews.

## Project Structure

| File | Description |
|------|-------------|
| `Puzzle.html` | Browser-based puzzle game (glassmorphism UI, Canvas, drag-and-drop) |
| `puzzle-builder.html` | Browser-based piece generator with download |
| `horse-puzzle.py` | Desktop GUI app (Tkinter) — main entry point |
| `jigsaw_puzzle_generator.py` | Core puzzle generation library (used by horse-puzzle.py) |

## Dependencies

- **Python**: `Pillow`, `numpy`, `tkinter` (built-in)
- **Browser**: No dependencies — JSZip loaded from CDN on demand

## How It Works

1. **Image upload** — user provides any image
2. **Grid division** — image split into rows x columns
3. **Edge generation** — for classic mode, Bezier curves create interlocking tab/blank edges
4. **Piece rendering** — each piece is cropped with alpha masking and drawn on Canvas
5. **Gameplay** — pieces are scattered randomly; drag them to the correct position (guided mode snaps within 30px)
6. **Completion** — confetti animation and timer stop when all pieces are placed
