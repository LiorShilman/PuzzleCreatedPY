# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Python desktop application that generates customizable jigsaw puzzle pieces from user-provided images. Supports classic interlocking-piece puzzles (Bezier curve edges) and simple rectangular grid puzzles. The UI is in **Hebrew (RTL)**.

## Running the Application

```bash
# GUI application (Tkinter)
python horse-puzzle.py

# Programmatic/headless usage
python -c "from jigsaw_puzzle_generator import createPuzzlePieces; createPuzzlePieces('image.jpg', 4, 6, 'output/')"
```

## Dependencies

Python 3 with: `Pillow` (PIL), `numpy`, `tkinter` (built-in). No requirements.txt exists — install manually:
```bash
pip install Pillow numpy
```

## Architecture

**Two main files with overlapping but distinct roles:**

- **`horse-puzzle.py`** — Full GUI application (Tkinter). Contains `PuzzleCreatorUI` class plus its own copy of the puzzle generation engine. This is the primary entry point.
- **`jigsaw_puzzle_generator.py`** — Standalone headless puzzle generation library. Duplicates core classes/functions from horse-puzzle.py for programmatic use without the GUI.

**Key classes (present in both files):**
- `PieceOutLine` — Generates Bezier curve outlines for interlocking piece edges
- `PieceInfo` — Manages piece positioning and border types (male/female/flat edge)

**Key functions:**
- `createPuzzlePieces(image, rows, cols, prefix)` — Classic jigsaw with interlocking Bezier edges
- `create_rectangular_pieces(image, rows, cols, prefix)` — Simple rectangular grid pieces
- `polygonCropImage(image, polygon)` — Crops image to arbitrary polygon using alpha masking
- `computeBezierPoint()` / `computerBezier()` — Cubic Bezier curve math

**Piece generation pipeline:** Image → grid division → border type assignment (t_FEMALE/t_MALE/t_LINE) → Bezier curve generation → polygon cropping with alpha mask → PNG/JPEG export

**Output** goes to `puzzle_pieces/` directory: individual `piece_[row]_[col].png` files plus `piece_outline_only.png` and `piece_outline_with_image.png`.

**Hardcoded tuning parameters** in horse-puzzle.py: `arcRatio` (0.07, arc depth), `connectRatio` (0.3, connector width), `pointNum` (300, Bezier curve resolution).

## Additional Interfaces

- **`Puzzle.html`** and **`puzzle-builder.html`** — Browser-based alternatives with dark theme, not connected to the Python backend.
- **`סוכן.txt`** — Hebrew-language instructions for GPT agents describing the puzzle creation workflow.

## Notes

- The GUI labels and button text are in Hebrew. The codebase has a nested `PuzzleCreatedPY/` subdirectory that appears to be a duplicate copy.
- There are no tests, no linter config, and no build system.
