#!/usr/bin/env python3
"""Regenerate every file in this repo that is derived from a source logo SVG.

There are two independent source vectors, each hand-edited directly (not
derived from anything):

  - haszcze-logo.svg              the standard mark
  - haszcze-logo-supported-A.svg  same mark with a crossbar bracing the "A"

For each of those, this script derives a yellow-on-black variant and a
hazard-stripe variant. It also derives the email-signature emblem crops
(from the standard mark only) and can re-render the master
haszcze-logo.png raster.

Run this after editing either source SVG in Inkscape (or any other tool)
to keep the derived files in sync instead of hand-editing each one.

Usage:
    python3 scripts/regen.py            # regenerate all derived SVGs
    python3 scripts/regen.py --png      # also re-render haszcze-logo.png and
                                         # email-signature/haszcze-emblem.png
                                         # (needs Windows Chrome via WSL, see
                                         # email-signature/README.md)

Does NOT touch the two source SVGs themselves - those are edited by hand.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from svgpath import parse_path, subpath_bbox, subpaths_to_d  # noqa: E402

ROOT = Path(__file__).parent.parent
YELLOW = "#F5C400"
BLACK = "#1A1A1A"
VIEWBOX = "0 0 1254 1254"

# Source vectors, each edited by hand - everything else in this script is
# derived from one of these.
SOURCES = ["haszcze-logo", "haszcze-logo-supported-A"]

# bbox of the ink of the emblem alone (crane + burst + "HASZCZE"), measured
# off the original 1254x1254 raster, plus a 16px margin. The wordmark
# "Hackerspace Szczecin" sits below y=900 and falls outside this crop.
EMBLEM_VIEWBOX = "163 83 964 816"

# Any subpath whose bbox starts above this y is the emblem; below it, the
# "Hackerspace Szczecin" wordmark. There is a wide empty gap in both source
# files (~y 700 to ~y 920) between the two groups, so this only needs to
# land somewhere in that gap.
EMBLEM_TEXT_SPLIT_Y = 900

NS = {"svg": "http://www.w3.org/2000/svg"}


def load_d(svg_path: Path) -> str:
    tree = ET.parse(svg_path)
    path_el = tree.getroot().find(".//svg:path", NS)
    if path_el is None:
        raise SystemExit(f"{svg_path}: no <path> element found")
    return path_el.get("d")


def svg_doc(body: str, *, bg: str | None = None, viewbox: str = VIEWBOX) -> str:
    bg_rect = f'<rect width="1254" height="1254" fill="{bg}"/>' if bg else ""
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="{viewbox}">{bg_rect}{body}</svg>\n'
    )


def stripes_body(emblem_d: str, wordmark_d: str) -> str:
    defs = (
        '<defs><pattern id="hz" width="120" height="120" patternUnits="userSpaceOnUse" '
        'patternTransform="rotate(45)">'
        f'<rect width="120" height="120" fill="{YELLOW}"/>'
        f'<rect width="60" height="120" fill="{BLACK}"/>'
        "</pattern></defs>"
    )
    return (
        defs
        + f'<path fill="url(#hz)" fill-rule="evenodd" d="{emblem_d}"/>'
        + f'<path fill="{BLACK}" fill-rule="evenodd" d="{wordmark_d}"/>'
    )


def write(path: Path, content: str) -> None:
    path.write_text(content)
    print(f"wrote {path.relative_to(ROOT)}")


def regen_source(name: str) -> tuple[str, list, list]:
    """Regenerate the yellow-on-black and stripe variants for one source.

    Returns (normalized_d, emblem_subpaths, wordmark_subpaths) so the caller
    can reuse the emblem split (needed for the email-signature crop, which
    is only derived from the standard mark).
    """
    d = load_d(ROOT / f"{name}.svg")
    subpaths = parse_path(d)
    d_normalized = subpaths_to_d(subpaths)

    write(
        ROOT / f"{name}-yellow-on-black.svg",
        svg_doc(f'<path fill="{YELLOW}" fill-rule="evenodd" d="{d_normalized}"/>', bg=BLACK),
    )

    emblem = [sp for sp in subpaths if subpath_bbox(sp)[1] <= EMBLEM_TEXT_SPLIT_Y]
    wordmark = [sp for sp in subpaths if subpath_bbox(sp)[1] > EMBLEM_TEXT_SPLIT_Y]
    write(
        ROOT / f"{name}-stripes.svg",
        svg_doc(stripes_body(subpaths_to_d(emblem), subpaths_to_d(wordmark))),
    )

    return d_normalized, emblem, wordmark


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--png", action="store_true",
        help="also re-render haszcze-logo.png and "
             "email-signature/haszcze-emblem.png (needs Windows Chrome via "
             "WSL interop)",
    )
    args = parser.parse_args()

    base_d = None
    base_emblem = None
    for name in SOURCES:
        d_normalized, emblem, _wordmark = regen_source(name)
        if name == "haszcze-logo":
            base_d = d_normalized
            base_emblem = emblem

    # Email-signature emblem crops (viewBox crop, no geometry change) -
    # derived from the standard mark only.
    emblem_d = subpaths_to_d(base_emblem)
    sig_dir = ROOT / "email-signature"
    write(
        sig_dir / "haszcze-emblem.svg",
        svg_doc(f'<path fill="{BLACK}" fill-rule="evenodd" d="{emblem_d}"/>', viewbox=EMBLEM_VIEWBOX),
    )
    write(
        sig_dir / "haszcze-emblem-yellow.svg",
        svg_doc(f'<path fill="{YELLOW}" fill-rule="evenodd" d="{emblem_d}"/>', viewbox=EMBLEM_VIEWBOX),
    )

    if args.png:
        render_png(
            svg_body=f'<path fill="{BLACK}" fill-rule="evenodd" d="{base_d}"/>',
            width=1254, height=1254, out=ROOT / "haszcze-logo.png",
            bg="#ffffff",
        )
        render_emblem_png(sig_dir)
    else:
        print("skipped haszcze-logo.png / haszcze-emblem.png (pass --png to re-render them)")


def _chrome_available() -> str | None:
    chrome = "/mnt/c/Program Files/Google/Chrome/Application/chrome.exe"
    if Path("/mnt/c/Users/Public").exists() and Path(chrome).exists():
        return chrome
    return None


def render_png(*, svg_body: str, width: int, height: int, out: Path, bg: str) -> None:
    """Render an inline SVG path to a PNG via headless Windows Chrome (WSL
    interop). Mirrors email-signature/README.md's documented method."""
    chrome = _chrome_available()
    if not chrome:
        print(f"WARNING: Windows Chrome / /mnt/c not available - skipping {out.name}.")
        return

    win_public = Path("/mnt/c/Users/Public")
    svg = svg_doc(svg_body, viewbox=f"0 0 {width} {height}")
    stem = out.stem
    (win_public / f"{stem}.svg").write_text(svg)
    render_html = (
        f"<!DOCTYPE html><html><body style='margin:0;background:{bg}'>"
        f"<img src='{stem}.svg' "
        f"style='display:block;width:{width}px;height:{height}px'></body></html>"
    )
    (win_public / f"render-{stem}.html").write_text(render_html)

    subprocess.run(
        [
            chrome, "--headless", "--disable-gpu", "--hide-scrollbars",
            f"--screenshot=C:\\Users\\Public\\{stem}.png",
            f"--window-size={width},{height}",
            f"file:///C:/Users/Public/render-{stem}.html",
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    out.write_bytes((win_public / f"{stem}.png").read_bytes())
    print(f"wrote {out.relative_to(ROOT)}")


def render_emblem_png(sig_dir: Path) -> None:
    """Render haszcze-emblem.svg to a 150x127 transparent PNG via headless
    Windows Chrome (WSL interop). Mirrors email-signature/README.md."""
    chrome = _chrome_available()
    if not chrome:
        print("WARNING: Windows Chrome / /mnt/c not available - "
              "skipping email-signature/haszcze-emblem.png. See "
              "email-signature/README.md for manual instructions "
              "(e.g. rsvg-convert).")
        return

    win_public = Path("/mnt/c/Users/Public")
    svg_src = (sig_dir / "haszcze-emblem.svg").read_text()
    (win_public / "haszcze-emblem.svg").write_text(svg_src)
    render_html = (
        "<!DOCTYPE html><html><body style='margin:0'>"
        "<img src='haszcze-emblem.svg' "
        "style='display:block;width:150px;height:127px'></body></html>"
    )
    (win_public / "render-emblem.html").write_text(render_html)

    subprocess.run(
        [
            chrome, "--headless", "--disable-gpu", "--hide-scrollbars",
            "--default-background-color=00000000",
            "--screenshot=C:\\Users\\Public\\haszcze-emblem.png",
            "--window-size=150,127",
            "file:///C:/Users/Public/render-emblem.html",
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    out = sig_dir / "haszcze-emblem.png"
    out.write_bytes((win_public / "haszcze-emblem.png").read_bytes())
    print(f"wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
