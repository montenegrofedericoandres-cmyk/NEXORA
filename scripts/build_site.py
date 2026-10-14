"""Build only public files after checking that prelaunch restrictions hold."""
from pathlib import Path
from shutil import copyfile
from check_site import validate

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "dist"
PUBLIC_FILES = {"index.html", "404.html", "_headers", ".assetsignore"}

validate((ROOT / "index.html").read_text(encoding="utf-8"))
OUTPUT.mkdir(exist_ok=True)
unexpected = {path.name for path in OUTPUT.iterdir()} - PUBLIC_FILES
if unexpected:
    raise SystemExit("Refusing to publish unexpected files: " + ", ".join(sorted(unexpected)))
for name in PUBLIC_FILES:
    copyfile(ROOT / name, OUTPUT / name)
print("PASS: static site built in dist/; no payment files, backend, or secrets published")
