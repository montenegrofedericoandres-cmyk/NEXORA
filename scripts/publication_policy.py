"""Safety rules shared by Cloudflare builds and CI; no external dependencies."""
import json
from pathlib import Path

PUBLIC_FILES = frozenset({"index.html", "404.html", "_headers", ".assetsignore"})
IGNORE_RULES = ["*", "!index.html", "!404.html", "!_headers"]
REQUIRED_HEADERS = {
    "x-content-type-options": "nosniff",
    "x-frame-options": "DENY",
    "referrer-policy": "no-referrer",
    "permissions-policy": "camera=(), microphone=(), geolocation=()",
    "content-security-policy": "default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "Duplicate Wrangler configuration key: " + key)
        result[key] = value
    return result


def validate_sources(root):
    root = Path(root).resolve()
    for name in PUBLIC_FILES | {"wrangler.jsonc"}:
        source = root / name
        require(source.is_file() and not source.is_symlink(), "Source must be a regular file: " + name)
    config = json.loads((root / "wrangler.jsonc").read_text(encoding="utf-8"), object_pairs_hook=unique_object)
    require(isinstance(config, dict), "Wrangler configuration must be an object")
    permitted = {"$schema", "name", "compatibility_date", "workers_dev", "preview_urls", "build", "assets"}
    require(not set(config) - permitted, "Only the reviewed static deployment options are allowed")
    assets = config.get("assets", {})
    build = config.get("build", {})
    require(isinstance(assets, dict) and isinstance(build, dict), "Missing static assets/build configuration")
    require(isinstance(assets.get("directory"), str), "Missing public asset directory")
    require((root / assets["directory"]).resolve() == root / "dist", "Publish dist only, never the repository root")
    require(build.get("command") == "python3 scripts/build_site.py", "Prelaunch validation must run before upload")
    require(assets.get("not_found_handling") == "404-page", "Missing files must return HTTP 404")
    require(set(assets) <= {"directory", "not_found_handling"}, "Only reviewed static asset options are allowed")
    require(config.get("name") == "nexora" and config.get("workers_dev") is True, "Keep the intended public static deployment")
    require(config.get("preview_urls") is False, "Version preview URLs must remain disabled")
    rules = [line.strip() for line in (root / ".assetsignore").read_text().splitlines() if line.strip() and not line.strip().startswith("#")]
    require(rules == IGNORE_RULES, "Only the reviewed public files may bypass the asset exclusion")
    lines = [line for line in (root / "_headers").read_text().splitlines() if line.strip()]
    require(lines and lines[0] == "/*", "Security headers must cover every static response")
    headers = {}
    for line in lines[1:]:
        require(line.startswith(" ") and ":" in line, "Only the reviewed global header rule is allowed")
        name, value = line.strip().split(":", 1)
        name = name.lower()
        require(name not in headers, "Duplicate response header: " + name)
        headers[name] = " ".join(value.split())
    for name, value in REQUIRED_HEADERS.items():
        require(headers.get(name) == value, "Required prelaunch response header changed: " + name)


def validate_output(root):
    root = Path(root).resolve()
    output = root / "dist"
    require(output.is_dir() and not output.is_symlink(), "Build output must be a regular dist directory")
    require({file.name for file in output.iterdir()} == PUBLIC_FILES, "Unexpected files in publication output")
    for name in PUBLIC_FILES:
        file = output / name
        require(file.is_file() and not file.is_symlink(), "No directories or symlinks may be published")
        require(file.read_bytes() == (root / name).read_bytes(), "Build artifact differs from its reviewed source: " + name)
