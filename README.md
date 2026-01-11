# streak-gen (Step 1)

Generate a single letter in a chosen font, subdivided into exactly N regions
(stained-glass style), and output a printable SVG.

## Setup (uv)
uv venv
uv pip install -e .

## Run
streak-gen gen-letter \
  --letter J \
  --font /path/to/font.ttf \
  --segments 12 \
  --out out/J_12.svg
