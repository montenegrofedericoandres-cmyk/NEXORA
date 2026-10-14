"""Build only public files after checking that prelaunch restrictions hold."""
from pathlib import Path
from shutil import copyfile
from check_site import validate
from publication_policy import PUBLIC_FILES, require, validate_output, validate_sources

ROOT = Path(__file__).resolve().parents[1]


def build(root=ROOT):
    root = Path(root).resolve()
    validate_sources(root)
    validate((root / "index.html").read_text(encoding="utf-8"))
    validate((root / "404.html").read_text(encoding="utf-8"), homepage=False)
    output = root / "dist"
    require(not output.is_symlink(), "Build output cannot be a symlink")
    output.mkdir(exist_ok=True)
    unexpected = {path.name for path in output.iterdir()} - PUBLIC_FILES
    require(not unexpected, "Refusing to publish unexpected files: " + ", ".join(sorted(unexpected)))
    for name in PUBLIC_FILES:
        target = output / name
        require(not target.is_symlink() and (not target.exists() or target.is_file()), "Unsafe artifact path: " + name)
    for name in PUBLIC_FILES:
        copyfile(root / name, output / name)
    validate_output(root)


if __name__ == "__main__":
    try:
        build()
    except (OSError, ValueError) as error:
        raise SystemExit("FAIL: " + str(error))
    print("PASS: both pages, output directory, exclusion rules and security headers validated before publication")
