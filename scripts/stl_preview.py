#!/usr/bin/env python3
"""Build a browser viewer (and optional PNG previews) for the 3D models in stl/.

The models are Bambu Studio project files (.3mf), i.e. zip containers with the
mesh in 3MF core XML inside. This script reads them with nothing but the Python
standard library, and writes:

  stl/viewer.html      one self-contained page (meshes embedded as base64
                       float32/uint32 buffers, no CDN, works over file://)
  stl/previews/*.png   one still per model, named and captioned with the
                       commit the source .3mf currently sits at (needs
                       headless Chrome). Stills from older commits are
                       deleted, so the folder always shows today's models.

Usage:
    python3 scripts/stl_preview.py           # rebuild stl/viewer.html
    python3 scripts/stl_preview.py --png     # also re-render stl/previews/*.png
                                             # (needs Windows Chrome via WSL,
                                             # see email-signature/README.md)

Both outputs are generated - do not hand-edit them. The viewer's markup lives
in scripts/stl_viewer.html.tmpl; only the model payload is injected here.
"""
from __future__ import annotations

import argparse
import base64
import json
import re
import struct
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).parent.parent
STL_DIR = ROOT / "stl"
PREVIEW_DIR = STL_DIR / "previews"
TEMPLATE = Path(__file__).parent / "stl_viewer.html.tmpl"

# Preview stills are rendered at this size, from this orbit angle (radians,
# same convention as the viewer: yaw around +Z, pitch above the XY plane).
SHOT_SIZE = (1200, 900)
SHOT_YAW = -0.9
SHOT_PITCH = 0.55

VERTEX_RE = re.compile(r'<vertex[^>]*\bx="([^"]+)"[^>]*\by="([^"]+)"[^>]*\bz="([^"]+)"')
TRIANGLE_RE = re.compile(r'<triangle[^>]*\bv1="(\d+)"[^>]*\bv2="(\d+)"[^>]*\bv3="(\d+)"')
COMPONENT_RE = re.compile(r'<component\b[^>]*>')
ATTR_RE = re.compile(r'(\w+(?::\w+)?)="([^"]*)"')


def parse_transform(text: str) -> tuple[float, ...] | None:
    """3MF stores a 4x3 matrix as 12 numbers, row-major, applied to a row
    vector: v' = v * M + t. Returns (m00..m22, t0, t1, t2)."""
    if not text:
        return None
    nums = tuple(float(n) for n in text.split())
    return nums if len(nums) == 12 else None


def apply_transform(verts: list[tuple[float, float, float]], m) -> list[tuple[float, float, float]]:
    if m is None:
        return verts
    a, b, c, d, e, f, g, h, i, tx, ty, tz = m
    return [
        (x * a + y * d + z * g + tx, x * b + y * e + z * h + ty, x * c + y * f + z * i + tz)
        for x, y, z in verts
    ]


def read_mesh(path: Path):
    """Pull the first mesh out of a .3mf, with the build/component transforms
    that place it on the plate already applied."""
    with zipfile.ZipFile(path) as z:
        root_doc = z.read("3D/3dmodel.model").decode("utf-8")

        # The mesh may live in the root document or (Bambu's habit) in a
        # separate part referenced by <component p:path="...">.
        mesh_doc, chain = root_doc, []
        comp = COMPONENT_RE.search(root_doc)
        if comp:
            attrs = dict(ATTR_RE.findall(comp.group(0)))
            chain.append(parse_transform(attrs.get("transform", "")))
            part = attrs.get("p:path") or attrs.get("path")
            if part:
                mesh_doc = z.read(part.lstrip("/")).decode("utf-8")

        item = re.search(r"<item\b[^>]*>", root_doc)
        if item:
            chain.append(parse_transform(dict(ATTR_RE.findall(item.group(0))).get("transform", "")))

    verts = [(float(x), float(y), float(z)) for x, y, z in VERTEX_RE.findall(mesh_doc)]
    tris = [(int(a), int(b), int(c)) for a, b, c in TRIANGLE_RE.findall(mesh_doc)]
    if not verts or not tris:
        raise SystemExit(f"{path.name}: no mesh found (vertices={len(verts)} triangles={len(tris)})")

    for m in chain:
        verts = apply_transform(verts, m)
    return verts, tris


def git_info(path: Path) -> dict:
    """Commit the file currently sits at, plus whether the working tree copy
    differs from it (so a preview can never silently claim to be that commit)."""
    def git(*args: str) -> str:
        out = subprocess.run(["git", "-C", str(ROOT), *args],
                             capture_output=True, text=True)
        return out.stdout.strip() if out.returncode == 0 else ""

    rel = str(path.relative_to(ROOT))
    line = git("log", "-1", "--format=%h\x1f%ad\x1f%s", "--date=short", "--", rel)
    dirty = bool(git("status", "--porcelain", "--", rel))
    if not line:
        return {"hash": "niezacommitowany", "date": "-", "subject": "-", "dirty": True}
    h, date, subject = line.split("\x1f")
    return {"hash": h, "date": date, "subject": subject, "dirty": dirty}


def preview_name(model: dict) -> str:
    """Preview filename carries the short commit of its source .3mf, so a
    render can never be mistaken for one of a different revision."""
    c = model["commit"]
    return f"{model['name']}-{c['hash']}{'-dirty' if c['dirty'] else ''}.png"


def b64(fmt: str, values) -> str:
    return base64.b64encode(struct.pack(f"<{len(values)}{fmt}", *values)).decode("ascii")


def build_model(path: Path) -> dict:
    verts, tris = read_mesh(path)
    lo = [min(v[i] for v in verts) for i in range(3)]
    hi = [max(v[i] for v in verts) for i in range(3)]
    flat_pos = [c for v in verts for c in v]
    flat_idx = [i for t in tris for i in t]
    print(f"{path.name}: {len(verts)} vertices, {len(tris)} triangles, "
          f"{hi[0]-lo[0]:.1f} x {hi[1]-lo[1]:.1f} x {hi[2]-lo[2]:.1f} mm")
    return {
        "name": path.stem,
        "file": path.name,
        "bytes": path.stat().st_size,
        "tris": len(tris),
        "center": [(lo[i] + hi[i]) / 2 for i in range(3)],
        "size": [hi[i] - lo[i] for i in range(3)],
        "commit": git_info(path),
        "pos": b64("f", flat_pos),
        "idx": b64("I", flat_idx),
    }


def write_viewer(models: list[dict]) -> Path:
    html = TEMPLATE.read_text(encoding="utf-8").replace(
        "/*MODELS*/", json.dumps(models, ensure_ascii=False, separators=(",", ":"))
    )
    out = STL_DIR / "viewer.html"
    out.write_text(html, encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT)} ({out.stat().st_size // 1024} kB)")
    return out


def chrome() -> str | None:
    exe = "/mnt/c/Program Files/Google/Chrome/Application/chrome.exe"
    if Path("/mnt/c/Users/Public").exists() and Path(exe).exists():
        return exe
    return None


def render_previews(viewer: Path, models: list[dict]) -> None:
    """Screenshot the viewer in its caption-only mode, once per model."""
    exe = chrome()
    if not exe:
        print("WARNING: Windows Chrome / /mnt/c not available - skipping stl/previews/*.png.")
        return

    public = Path("/mnt/c/Users/Public")
    staged = public / "haszcze-stl-viewer.html"
    staged.write_text(viewer.read_text(encoding="utf-8"), encoding="utf-8")
    PREVIEW_DIR.mkdir(exist_ok=True)
    w, h = SHOT_SIZE
    keep = {preview_name(m) for m in models}

    for m in models:
        query = f"?shot={m['name']}&yaw={SHOT_YAW}&pitch={SHOT_PITCH}"
        subprocess.run(
            [
                exe, "--headless", "--hide-scrollbars",
                # SwiftShader: the viewer needs a working WebGL2 context and
                # headless Chrome has no GPU here.
                "--enable-unsafe-swiftshader", "--use-angle=swiftshader",
                "--virtual-time-budget=4000",
                f"--screenshot=C:\\Users\\Public\\haszcze-stl-{m['name']}.png",
                f"--window-size={w},{h}",
                f"file:///C:/Users/Public/haszcze-stl-viewer.html{query}",
            ],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        out = PREVIEW_DIR / preview_name(m)
        out.write_bytes((public / f"haszcze-stl-{m['name']}.png").read_bytes())
        print(f"wrote {out.relative_to(ROOT)}")

    # Everything else in previews/ is a still of an older commit (or of a
    # model that has since left stl/) - drop it rather than leave stale
    # renders lying around next to the current ones.
    for stale in sorted(PREVIEW_DIR.glob("*.png")):
        if stale.name not in keep:
            stale.unlink()
            print(f"removed {stale.relative_to(ROOT)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--png", action="store_true",
                        help="also re-render stl/previews/*.png (needs Windows Chrome via WSL)")
    args = parser.parse_args()

    sources = sorted(STL_DIR.glob("*.3mf"))
    if not sources:
        raise SystemExit(f"no .3mf files in {STL_DIR}")
    models = [build_model(p) for p in sources]
    viewer = write_viewer(models)

    if args.png:
        render_previews(viewer, models)
    else:
        print("skipped stl/previews/*.png (pass --png to re-render them)")


if __name__ == "__main__":
    main()
