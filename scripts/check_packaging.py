"""Prevent publishing the repository, credentials, or product downloads."""
from pathlib import Path
from publication_policy import validate_output, validate_sources

ROOT = Path(__file__).resolve().parents[1]
validate_sources(ROOT)
validate_output(ROOT)
print("PASS: public asset allowlist, dist-only upload, custom 404 and static-only Worker configuration")
