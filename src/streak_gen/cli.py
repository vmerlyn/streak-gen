from __future__ import annotations
import typer
from pathlib import Path
from .segmenter import segment_letter_to_regions, segment_word_to_regions
from .render_svg import render_letter_svg
from .layout_year import layout_year

app = typer.Typer(no_args_is_help=True)

@app.command("gen-letter")
def gen_letter(
    letter: str = typer.Option(..., "--letter", "-l"),
    font: Path = typer.Option(..., "--font", "-f", exists=True),
    segments: int = typer.Option(..., "--segments", "-n", min=1),
    out: Path = typer.Option(..., "--out", "-o"),
):
    # Uppercase the letter by default
    letter = letter.upper()

    result = segment_letter_to_regions(
        letter=letter,
        font_path=font,
        segments=segments,
        font_size=420.0,
        inset=6.0,
    )

    svg_text = render_letter_svg(
        page="letter",
        margin=36.0,
        outline_path_svg=result.outline_path_svg,
        regions=result.regions,
        labels=result.labels,
        voronoi_edges=result.voronoi_edges,
    )

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(svg_text, encoding="utf-8")
    typer.echo(f"Wrote: {out}")


@app.command("gen-word")
def gen_word(
    word: str = typer.Option(..., "--word", "-w"),
    font: Path = typer.Option(..., "--font", "-f", exists=True),
    segments: int = typer.Option(..., "--segments", "-n", min=1),
    out: Path = typer.Option(..., "--out", "-o"),
):
    # Uppercase the word by default
    word = word.upper()

    result = segment_word_to_regions(
        word=word,
        font_path=font,
        segments=segments,
        font_size=420.0,
        inset=6.0,
    )

    svg_text = render_letter_svg(
        page="letter",
        margin=36.0,
        outline_path_svg=result.outline_path_svg,
        regions=result.regions,
        labels=result.labels,
        voronoi_edges=result.voronoi_edges,
    )

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(svg_text, encoding="utf-8")
    typer.echo(f"Wrote: {out}")


@app.command("gen-calendar")
def gen_calendar(
    font: Path = typer.Option(..., "--font", "-f", exists=True),
    out: Path = typer.Option("calendar.svg", "--out", "-o"),
):
    """Generate year calendar with all 12 months. Only adjustable option is font."""
    layout_year(font, out)
    typer.echo(f"Calendar generated: {out}")


@app.command("gen-year")
def gen_year(
    font: Path = typer.Option(..., "--font", "-f", exists=True),
    out: Path = typer.Option("out/year_calendar.svg", "--out", "-o"),
):
    """Generate all 12 months on a single letter-sized page."""
    layout_year(font, out)
    typer.echo(f"Year calendar generated: {out}")


if __name__ == "__main__":
    app()
