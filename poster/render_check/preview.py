"""Render the artboards as plain HTML (no DC runtime) to check layout locally.
The markup is literal -- no holes, loops or imports -- so the plain render is faithful.
Uploaded assets are swapped for their local source files."""
import json, pathlib
root = pathlib.Path(__file__).resolve().parent.parent
src = root / "canvas" / "project"
assets = json.loads((root / "assets.json").read_text())
out = pathlib.Path(__file__).resolve().parent / "out"
out.mkdir(exist_ok=True)
for name in ("Left", "Main", "Right"):
    h = (src / f"{name}.dc.html").read_text()
    body = h[h.index("<x-dc>") + 6:h.index("</x-dc>")]
    body = body.replace("<helmet>", "").replace("</helmet>", "")
    for fname, blob in assets.items():
        body = body.replace(blob, "file://" + str(root / "assets" / fname))
    (out / f"{name}.html").write_text(
        f'<!doctype html><html><head><meta charset="utf-8"></head><body>{body}</body></html>')
