#!/bin/bash
# Generate all 12 months with correct day counts

set -e

FONT="fonts/CooperBlack.ttf"
OUT_DIR="out/months"

# Create output directory
mkdir -p "$OUT_DIR"

echo "Generating month calendars..."

# Generate each month with its day count
streak-gen gen-word --word january --font "$FONT" --segments 31 --out "$OUT_DIR/01_JANUARY_31.svg"
echo "✓ January (31 days)"

streak-gen gen-word --word february --font "$FONT" --segments 28 --out "$OUT_DIR/02_FEBRUARY_28.svg"
echo "✓ February (28 days)"

streak-gen gen-word --word march --font "$FONT" --segments 31 --out "$OUT_DIR/03_MARCH_31.svg"
echo "✓ March (31 days)"

streak-gen gen-word --word april --font "$FONT" --segments 30 --out "$OUT_DIR/04_APRIL_30.svg"
echo "✓ April (30 days)"

streak-gen gen-word --word may --font "$FONT" --segments 31 --out "$OUT_DIR/05_MAY_31.svg"
echo "✓ May (31 days)"

streak-gen gen-word --word june --font "$FONT" --segments 30 --out "$OUT_DIR/06_JUNE_30.svg"
echo "✓ June (30 days)"

streak-gen gen-word --word july --font "$FONT" --segments 31 --out "$OUT_DIR/07_JULY_31.svg"
echo "✓ July (31 days)"

streak-gen gen-word --word august --font "$FONT" --segments 31 --out "$OUT_DIR/08_AUGUST_31.svg"
echo "✓ August (31 days)"

streak-gen gen-word --word september --font "$FONT" --segments 30 --out "$OUT_DIR/09_SEPTEMBER_30.svg"
echo "✓ September (30 days)"

streak-gen gen-word --word october --font "$FONT" --segments 31 --out "$OUT_DIR/10_OCTOBER_31.svg"
echo "✓ October (31 days)"

streak-gen gen-word --word november --font "$FONT" --segments 30 --out "$OUT_DIR/11_NOVEMBER_30.svg"
echo "✓ November (30 days)"

streak-gen gen-word --word december --font "$FONT" --segments 31 --out "$OUT_DIR/12_DECEMBER_31.svg"
echo "✓ December (31 days)"

echo ""
echo "✓ All 12 months generated in $OUT_DIR"
echo "Total files: $(ls -1 "$OUT_DIR" | wc -l)"

echo ""
echo "Generating year calendar (all 12 months on one page)..."
streak-gen gen-year --font "$FONT" --out "out/year_calendar.svg"
echo "✓ Year calendar generated: out/year_calendar.svg"
