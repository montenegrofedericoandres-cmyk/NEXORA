from pathlib import Path
from html.parser import HTMLParser
import sys

class Check(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.has_title = False
        self.lang_es = False
    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == "html" and d.get("lang") == "es": self.lang_es = True
        if tag == "title": self.has_title = True
        if tag == "a": self.links.append(d.get("href", ""))

p = Path("index.html")
assert p.exists(), "Missing index.html"
html = p.read_text(encoding="utf-8")
parser = Check()
parser.feed(html)
assert parser.lang_es, "Missing Spanish language tag"
assert parser.has_title, "Missing title"
assert "nexoraproductosdigitales@gmail.com" in html, "Missing support contact"
assert "NEXORA" in html, "Missing brand"
assert not any("mpago.la" in href for href in parser.links), "Checkout must remain disabled until verified"
assert not any(href.lower().startswith("javascript:") for href in parser.links), "Unsafe link"
assert not any(s in html.lower() for s in ("access_token=", "mp_access_token", "webhook_secret")), "Possible secret"
print("PASS: prelaunch site checks")
