# /// script
# requires-python = ">=3.10"
# dependencies = ["schemdraw", "matplotlib", "pillow"]
# ///
"""Thin helper library for schemdraw with workarounds for common gotchas.

Gotchas addressed:
- Transparent background: schemdraw renders with transparent bg by default;
  save_drawing() composites onto white via PIL.
- Cursor drift: add_ground() uses explicit .at() positioning instead of
  relying on the implicit drawing cursor.
- Label overlap: add_label() uses elm.Annotate with explicit coordinate
  offsets to avoid collisions with component bodies.
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import schemdraw
import schemdraw.elements as elm
from PIL import Image


def save_drawing(
    drawing: schemdraw.Drawing,
    path: str | Path,
    dpi: int = 150,
    title: str | None = None,
) -> None:
    """Render a schemdraw Drawing to an image file with a white background.

    Uses PIL to composite the RGBA output onto white, working around
    schemdraw's default transparent background.
    """
    fig = drawing.draw().get_figure()
    if title is not None:
        fig.suptitle(title)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, transparent=True, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)

    rgba = Image.open(buf).convert("RGBA")
    white = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
    composite = Image.alpha_composite(white, rgba)
    composite.convert("RGB").save(path, dpi=(dpi, dpi))


def add_ground(
    drawing: schemdraw.Drawing,
    element: schemdraw.elements.Element,
    pin: str = "end",
) -> schemdraw.elements.Element:
    """Add a ground symbol at an explicit pin, avoiding cursor-drift gotcha."""
    anchor = getattr(element, pin)
    return drawing.add(elm.Ground().at(anchor))


def add_label(
    drawing: schemdraw.Drawing,
    element: schemdraw.elements.Element,
    text: str,
    offset: float = 1.5,
    side: str = "left",
) -> schemdraw.elements.Element:
    """Add an annotation label offset from an element's center.

    side: "left" (-x), "right" (+x), "above" (+y), "below" (-y).
    """
    cx, cy = element.center
    dx, dy = {
        "left": (-offset, 0),
        "right": (offset, 0),
        "above": (0, offset),
        "below": (0, -offset),
    }[side]
    return drawing.add(
        elm.Annotate().at((cx + dx, cy + dy)).label(text)
    )


def main() -> None:
    """Draw a simple Vin → R1 → C1 → GND demo circuit."""
    out = sys.argv[1] if len(sys.argv) > 1 else "/tmp/schemdraw_demo.png"

    with schemdraw.Drawing() as d:
        vin = d.add(elm.SourceSin().up().label("Vin", loc="left"))
        r1 = d.add(elm.Resistor().right().label("R1\n1 kΩ"))
        c1 = d.add(elm.Capacitor().down().label("C1\n100 nF", loc="left"))
        d.add(elm.Line().left().tox(vin.start))
        add_ground(d, c1, pin="end")

    save_drawing(d, out, title="RC Lowpass — schemdraw demo")
    print(f"Saved to {out}")


if __name__ == "__main__":
    main()
