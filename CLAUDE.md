# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**streak-gen** generates stained-glass style segmented letters as printable SVG files. Given a letter, a font file, and a target number of segments, it creates an SVG with the letter subdivided into exactly N regions (like stained glass).
Eventually we want to be able to generate words and multiple words, bootstrapping off of letters.

## Setup and Installation

```bash
# Setup with uv
uv venv
uv pip install -e .
```

## Commands

### Generate a letter SVG
```bash
streak-gen gen-letter \
  --letter J \
  --font /path/to/font.ttf \
  --segments 12 \
  --out out/J_12.svg
```

## Architecture

The processing pipeline follows these stages:

1. **Font Processing** (`font_outline.py`)
   - Uses `skia-python` to extract glyph outlines from TrueType fonts
   - `glyph_outline_svg_path()`: Converts letter to Skia Path and SVG path string
   - `skia_path_to_polygon()`: Converts Skia Path to Shapely Polygon (not implemented)

2. **Seed Generation** (`seeds.py`)
   - Generates N random points uniformly distributed within the letter's polygon
   - Uses rejection sampling with configurable RNG seed (currently hardcoded to 0)

3. **Voronoi Segmentation** (`voronoi.py`)
   - Computes Voronoi diagram from seed points (not implemented)
   - Clips Voronoi cells to letter boundary to create exactly N regions

4. **Rendering** (`render_svg.py`)
   - Generates printable letter-sized SVG (612×792 points)
   - Renders regions, letter outline, and region labels

5. **CLI** (`cli.py`)
   - Single command: `gen-letter` orchestrates the full pipeline
   - Hardcoded parameters: `font_size=420.0`, `inset=6.0`

### Data Flow

`cli.py` → `segmenter.segment_letter_to_regions()` → `render_svg.render_letter_svg()` → SVG file

Core data structures (`types.py`):
- `Region`: polygon with ID
- `Label`: text label positioned at a point
- `SegmentationResult`: complete output of segmentation (outline, regions, labels)

## Current State

This is **Step 1** of development. Core pipeline structure is in place but three key functions remain unimplemented:
- `skia_path_to_polygon()` in `font_outline.py`
- `voronoi_cells()` in `voronoi.py`
- Region rendering logic in `render_svg.py` (loop is empty)

The `segmenter.py` currently raises `NotImplementedError` after generating seed points.
