"""Prevent publishing the repository, credentials, or product downloads."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
config = json.loads((ROOT / "wrangler.jsonc").read_text(encoding="utf-8"))
assert (ROOT / config["assets"]["directory"]).resolve() == ROOT / "dist", "Publish dist only, never the repository root"
assert config["build"]["command"] == "python3 scripts/build_site.py", "Prelaunch validation must run before upload"
assert config["assets"]["not_found_handling"] == "404-page", "Missing files must return HTTP 404"
assert config["preview_urls"] is False, "Do not leave old version preview URLs public"
assert "main" not in config, "This deployment must use static assets without a Worker script"
assert not any(key in config for key in ("r2_buckets", "d1_databases", "kv_namespaces", "services", "durable_objects")), "No backend resources are needed for prelaunch"
expected = {"index.html", "404.html", "_headers", ".assetsignore"}
output = ROOT / "dist"
assert {file.name for file in output.iterdir()} == expected, "Unexpected files in publication output"
assert all(file.is_file() and not file.is_symlink() for file in output.iterdir()), "No directories or symlinks may be published"
rules = [line.strip() for line in (ROOT / ".assetsignore").read_text().splitlines() if line.strip() and not line.startswith("#")]
assert rules == ["*", "!index.html", "!404.html", "!_headers"], "Root fallback must exclude all files except the two HTML pages and headers"
assert (output / ".assetsignore").read_bytes() == (ROOT / ".assetsignore").read_bytes()
print("PASS: public asset allowlist, dist-only upload, custom 404 and static-only Worker configuration")
