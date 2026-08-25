"""Minimal, dependency-free SVG path ('d' attribute) parser and re-serializer.

Only supports the commands potrace/Inkscape actually emit for this logo:
M/m, L/l, H/h, V/v, C/c, Z/z. Anything else raises ValueError rather than
silently producing wrong geometry.

Parsing resolves every command to absolute coordinates and expands H/V to L,
so the output is toolchain-independent and safe to slice into subpaths and
regroup (a subpath that started with a relative "m" referencing the previous
subpath's endpoint would otherwise break if moved to a different group).
"""
from __future__ import annotations

import re

_TOKEN_RE = re.compile(r"[MmLlHhVvCcZz]|-?\d*\.?\d+(?:[eE][-+]?\d+)?")

_ARGC = {"M": 2, "L": 2, "H": 1, "V": 1, "C": 6}


def _tokenize(d: str) -> list[str]:
    return _TOKEN_RE.findall(d)


def parse_path(d: str) -> list[list[tuple]]:
    """Parse a path 'd' string into a list of subpaths.

    Each subpath is a list of absolute segments:
    ("M", x, y) | ("L", x, y) | ("C", x1, y1, x2, y2, x, y) | ("Z",)
    """
    tokens = _tokenize(d)
    i, n = 0, len(tokens)
    cur = (0.0, 0.0)
    start = (0.0, 0.0)
    subpaths: list[list[tuple]] = []
    cur_sub: list[tuple] | None = None
    cmd = None

    def is_cmd(tok: str) -> bool:
        return tok in "MmLlHhVvCcZz"

    while i < n:
        tok = tokens[i]
        if is_cmd(tok):
            cmd = tok
            i += 1
        if cmd is None:
            raise ValueError(f"path data does not start with a command: {d[:40]!r}")
        upper = cmd.upper()
        rel = cmd.islower()

        if upper == "Z":
            cur_sub.append(("Z",))
            cur = start
            # Z takes no args; next token (if any) must be a new command.
            continue

        argc = _ARGC[upper]
        args = [float(tokens[i + k]) for k in range(argc)]
        i += argc

        if upper == "M":
            x, y = args
            if rel and cur_sub is not None:
                x, y = cur[0] + x, cur[1] + y
            cur = (x, y)
            start = cur
            cur_sub = [("M", *cur)]
            subpaths.append(cur_sub)
            # Subsequent coordinate pairs after an M (without a repeated
            # command letter) are implicit linetos.
            cmd = "l" if rel else "L"
        elif upper == "L":
            x, y = args
            if rel:
                x, y = cur[0] + x, cur[1] + y
            cur = (x, y)
            cur_sub.append(("L", *cur))
        elif upper == "H":
            (x,) = args
            if rel:
                x = cur[0] + x
            cur = (x, cur[1])
            cur_sub.append(("L", *cur))
        elif upper == "V":
            (y,) = args
            if rel:
                y = cur[1] + y
            cur = (cur[0], y)
            cur_sub.append(("L", *cur))
        elif upper == "C":
            x1, y1, x2, y2, x, y = args
            if rel:
                x1, y1 = cur[0] + x1, cur[1] + y1
                x2, y2 = cur[0] + x2, cur[1] + y2
                x, y = cur[0] + x, cur[1] + y
            cur_sub.append(("C", x1, y1, x2, y2, x, y))
            cur = (x, y)
        else:
            raise ValueError(f"unsupported command {cmd!r}")

    return subpaths


def _fmt(v: float) -> str:
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return s if s else "0"


def subpath_to_d(subpath: list[tuple]) -> str:
    parts = []
    for seg in subpath:
        if seg[0] == "M":
            parts.append(f"M{_fmt(seg[1])} {_fmt(seg[2])}")
        elif seg[0] == "L":
            parts.append(f"L{_fmt(seg[1])} {_fmt(seg[2])}")
        elif seg[0] == "C":
            parts.append(
                f"C{_fmt(seg[1])} {_fmt(seg[2])} {_fmt(seg[3])} {_fmt(seg[4])} "
                f"{_fmt(seg[5])} {_fmt(seg[6])}"
            )
        elif seg[0] == "Z":
            parts.append("Z")
    return "".join(parts)


def subpaths_to_d(subpaths: list[list[tuple]]) -> str:
    return "".join(subpath_to_d(sp) for sp in subpaths)


def subpath_bbox(subpath: list[tuple]) -> tuple[float, float, float, float]:
    """Approximate bbox using segment endpoints and cubic control points.

    Slightly wider than the true geometric bbox (control points can lie
    outside the curve), which is fine for classifying subpaths by rough
    vertical position - it never makes the box smaller than reality.
    """
    xs: list[float] = []
    ys: list[float] = []
    for seg in subpath:
        if seg[0] == "M" or seg[0] == "L":
            xs.append(seg[1])
            ys.append(seg[2])
        elif seg[0] == "C":
            xs.extend([seg[1], seg[3], seg[5]])
            ys.extend([seg[2], seg[4], seg[6]])
    return min(xs), min(ys), max(xs), max(ys)
