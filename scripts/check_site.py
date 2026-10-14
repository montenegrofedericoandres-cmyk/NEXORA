"""Validate the static prelaunch page without dependencies or network calls."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qsl, unquote, urlsplit
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
CONTACT = "nexoraproductosdigitales@gmail.com"


class Check(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.errors = []
        self.tags = []
        self.lang_es = False
        self.viewport = False
        self.viewport_count = 0
        self.in_title = False
        self.title = ""

    def handle_starttag(self, tag, attrs):
        if len({name for name, _ in attrs}) != len(attrs):
            self.errors.append("Duplicate HTML attributes are not allowed")
        attrs = dict(attrs)
        self.tags.append(tag)
        if tag == "html":
            self.lang_es = attrs.get("lang") == "es"
        if tag == "title":
            self.in_title = True
        if tag == "meta":
            if (attrs.get("name") or "").lower() == "viewport":
                self.viewport_count += 1
                self.viewport = "width=device-width" in (attrs.get("content") or "").replace(" ", "")
            if (attrs.get("http-equiv") or "").lower() == "refresh":
                self.errors.append("Automatic redirects are disabled during prelaunch")
        if tag in {"script", "iframe", "form", "input", "select", "textarea", "embed", "object", "base", "link"}:
            self.errors.append(f"External resources or interactive checkout are disabled: <{tag}>")
        if any(name.startswith("on") for name in attrs):
            self.errors.append("Inline event handlers are disabled during prelaunch")
        if "download" in attrs:
            self.errors.append("Digital deliveries must remain disabled")
        if tag in {"img", "audio", "video", "source"}:
            self.errors.append("Media must be reviewed before adding it to this static page")
        if tag == "a":
            href = attrs.get("href") or ""
            self.links.append(href)
            target = urlsplit(href)
            safe_email = target.scheme == "mailto" and unquote(target.path) == CONTACT
            if safe_email:
                params = parse_qsl(target.query, keep_blank_values=True)
                safe_email = len(params) <= 1 and all(key.lower() == "subject" for key, _ in params) and not target.fragment
            if re.search(r"[\x00-\x1f\x7f]", unquote(href)):
                self.errors.append("Control characters are not allowed in links")
            if not (href == "/" or href.startswith("#") or safe_email):
                self.errors.append("Only the verified contact address and same-page links are allowed; checkout and delivery links are disabled")

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title += data


def validate(html, *, homepage=True):
    parser = Check()
    parser.feed(html)
    errors = list(parser.errors)
    for valid, message in [
        (parser.lang_es and parser.tags.count("html") == 1, "Expected one Spanish language document"),
        ("NEXORA" in parser.title and parser.tags.count("title") == 1, "Expected one NEXORA page title"),
        (parser.viewport and parser.viewport_count == 1, "Expected one responsive viewport"),
        (parser.tags.count("h1") == 1, "Expected one main heading"),
        ("main" in parser.tags, "Missing main landmark"),
    ]:
        if not valid:
            errors.append(message)
    if homepage:
        if not any(href.startswith("mailto:" + CONTACT) for href in parser.links):
            errors.append("Missing support contact")
        if "Próximamente disponible." not in html:
            errors.append("Missing prelaunch notice")
    elif "/" not in parser.links or "todavía no habilitó ventas ni entregas." not in html:
        errors.append("404 page must explain prelaunch status and link to the homepage")
    if re.search(r"access_token\s*[=:]|mp_access_token|webhook_secret|sk-proj-|-----BEGIN (?:RSA )?PRIVATE KEY-----", html, re.I):
        errors.append("Possible secret in public HTML")
    if re.search(r"@import\b|url\s*\(", html, re.I):
        errors.append("CSS resource URLs require review before deployment")
    if errors:
        raise ValueError("\n".join(dict.fromkeys(errors)))


if __name__ == "__main__":
    try:
        validate((ROOT / "index.html").read_text(encoding="utf-8"))
        validate((ROOT / "404.html").read_text(encoding="utf-8"), homepage=False)
    except (OSError, ValueError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        sys.exit(1)
    print("PASS: homepage and 404 metadata, contact, and prelaunch payment/delivery checks")
