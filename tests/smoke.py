#!/usr/bin/env python3
"""Check the running Nginx site using only Python's standard library."""
import re
import sys
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit
from urllib.request import urlopen


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.add(attrs["id"])
        for key in ("src", "href"):
            if attrs.get(key):
                self.links.append(attrs[key])


def check(base):
    def get(path):
        with urlopen(urljoin(base, path), timeout=10) as response:
            assert response.status == 200, path
            return response.headers, response.read()

    headers, raw_id = get("/__node")
    node_id = raw_id.decode().strip()
    assert re.fullmatch(r"vm-[A-Za-z0-9-]+", node_id), node_id
    assert headers["X-Served-By"] == node_id
    assert "no-store" in headers["Cache-Control"]
    assert get("/healthz")[1] == b"ok\n"
    documents = {}
    for path in ("/index.html", "/collection.html", "/about.html"):
        headers, raw = get(path)
        html = raw.decode()
        assert headers["X-Served-By"] == node_id, path
        assert "text/html" in headers["Content-Type"]
        assert "<!--#" not in html and "[an error occurred" not in html, path
        footer = re.search(r'<code id="serving-node">\s*([^<]+?)\s*</code>', html)
        assert footer and footer.group(1).strip() == node_id, path
        document = Page()
        document.feed(html)
        documents[path] = document
    assets = set()
    for path, document in documents.items():
        for link in document.links:
            parsed = urlsplit(urljoin(base, link))
            assert parsed.netloc == urlsplit(base).netloc, link
            if parsed.path in documents:
                if parsed.fragment:
                    assert parsed.fragment in documents[parsed.path].ids, link
            else:
                assets.add(parsed.path)
    for asset in sorted(assets):
        assert get(asset)[1], asset
    print(f"PASS: 3 pages, {len(assets)} linked assets, anchors, health, SSI, headers; node={node_id}")


if __name__ == "__main__":
    check((sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080").rstrip("/") + "/")
