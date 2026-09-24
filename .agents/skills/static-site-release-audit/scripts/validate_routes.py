#!/usr/bin/env python3
"""Read-only structural validation for a local static-site public directory."""
from __future__ import annotations

import argparse
import html.parser
import json
import posixpath
import re
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_bool(value: str) -> bool:
    if value in {"true", "1", "yes"}:
        return True
    if value in {"false", "0", "no"}:
        return False
    raise ValueError(f"invalid boolean: {value}")


def origin(url: str) -> tuple[str, str, int] | None:
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        return None
    try:
        port = parsed.port
    except ValueError:
        return None
    scheme = parsed.scheme.lower()
    return scheme, parsed.hostname.lower(), port or (443 if scheme == "https" else 80)


def safe_path(root: Path, candidate: Path) -> Path | None:
    try:
        resolved = candidate.resolve()
        resolved.relative_to(root)
        return resolved
    except (OSError, ValueError):
        return None


def normalized_route(value: str) -> str | None:
    parsed = urllib.parse.urlsplit(value)
    if parsed.scheme or parsed.netloc:
        return None
    raw = urllib.parse.unquote(parsed.path or "/")
    if not raw.startswith("/"):
        return None
    parts = [part for part in raw.split("/") if part]
    if any(part in {".", ".."} for part in parts):
        return None
    path = "/" + "/".join(parts)
    if path == "/index.html":
        return "/"
    if path.endswith("/index.html"):
        path = path[:-11] or "/"
    return path.rstrip("/") or "/"


def route_candidates(route: str) -> list[str]:
    normalized = normalized_route(route)
    if normalized is None:
        return []
    relative = normalized.lstrip("/")
    if not relative:
        return ["index.html"]
    return [f"{relative}/index.html", f"{relative}.html", relative]


def file_for_route(root: Path, route: str) -> Path | None:
    for candidate in route_candidates(route):
        found = safe_path(root, root / candidate)
        if found and found.is_file():
            return found
    return None


class PageParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[str, str]] = []
        self.title = ""
        self.in_title = False
        self.meta: dict[str, str] = {}
        self.canonical = ""
        self.json_ld: list[str] = []
        self.in_json_ld = False
        self.json_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = {key.lower(): value or "" for key, value in attrs}
        if tag == "a" and data.get("href"):
            self.links.append(("route", data["href"]))
        elif tag in {"img", "script", "link", "source", "video", "audio", "iframe"}:
            for key in ("src", "href", "poster"):
                if data.get(key):
                    if tag == "link" and "canonical" in data.get("rel", "").lower().split():
                        self.canonical = data[key]
                    else:
                        self.links.append(("asset", data[key]))
        if tag == "meta":
            key = data.get("name") or data.get("property")
            if key:
                self.meta[key.lower()] = data.get("content", "")
        if tag == "title":
            self.in_title = True
        if tag == "script" and data.get("type", "").split(";", 1)[0].lower() == "application/ld+json":
            self.in_json_ld, self.json_text = True, []

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self.in_title = False
        if tag == "script" and self.in_json_ld:
            self.json_ld.append("".join(self.json_text))
            self.in_json_ld = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title += data
        if self.in_json_ld:
            self.json_text.append(data)


class Reporter:
    def __init__(self) -> None:
        self.blockers = 0

    def emit(self, severity: str, message: str) -> None:
        print(f"{severity} {message}")
        if severity == "BLOCKER":
            self.blockers += 1


def local_target(root: Path, page: Path, value: str, expected_origin: tuple[str, str, int] | None) -> tuple[Path | None, str | None]:
    parsed = urllib.parse.urlsplit(value)
    if parsed.scheme in {"mailto", "tel", "javascript", "data"} or value.startswith("#"):
        return None, None
    if parsed.scheme == "file":
        return None, "absolute filesystem URL"
    if parsed.scheme or parsed.netloc:
        if expected_origin is None or origin(value) != expected_origin:
            return None, None
        raw_path, base = urllib.parse.unquote(parsed.path or "/"), root
    else:
        raw_path, base = urllib.parse.unquote(parsed.path), root if parsed.path.startswith("/") else page.parent
    if not raw_path:
        return None, None
    resolved = safe_path(root, base / raw_path.lstrip("/") if base == root else base / raw_path)
    if resolved is None:
        return None, "reference escapes public root"
    return resolved, None


def target_exists(root: Path, target: Path, kind: str) -> bool:
    if target.is_file() or (target.is_dir() and (target / "index.html").is_file()):
        return True
    if kind != "route":
        return False
    try:
        return file_for_route(root, "/" + target.relative_to(root).as_posix()) is not None
    except ValueError:
        return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--routes-file", type=Path)
    parser.add_argument("--canonical-base", default="")
    parser.add_argument("--sitemap-file", default="sitemap.xml")
    parser.add_argument("--robots-file", default="robots.txt")
    parser.add_argument("--require-sitemap", default="false")
    parser.add_argument("--require-robots", default="false")
    parser.add_argument("--require-metadata", default="false")
    args = parser.parse_args()
    root, report = args.root.resolve(), Reporter()
    try:
        require_sitemap = parse_bool(args.require_sitemap)
        require_robots = parse_bool(args.require_robots)
        require_metadata = parse_bool(args.require_metadata)
    except ValueError as exc:
        report.emit("BLOCKER", str(exc))
        return 1
    expected_origin = origin(args.canonical_base) if args.canonical_base else None
    if args.canonical_base and expected_origin is None:
        report.emit("BLOCKER", "CANONICAL_BASE must be an absolute http or https origin")
        return 1
    sitemap = safe_path(root, root / args.sitemap_file)
    robots = safe_path(root, root / args.robots_file)
    if sitemap is None or robots is None:
        report.emit("BLOCKER", "sitemap or robots path escapes public root")
        return 1

    expected_routes: set[str] = set()
    metadata_pages: set[Path] | None = set() if args.routes_file else None
    if args.routes_file:
        for line in args.routes_file.read_text(encoding="utf-8").splitlines():
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            route = normalized_route(line.strip())
            if route is None:
                report.emit("BLOCKER", f"invalid expected route: {line.strip()}")
                continue
            expected_routes.add(route)
            page_for_route = file_for_route(root, route)
            if page_for_route is None:
                report.emit("BLOCKER", f"expected route has no local page: {route}")
            else:
                metadata_pages.add(page_for_route)
        report.emit("INFO", f"checked {len(expected_routes)} expected public routes")

    pages = sorted(root.rglob("*.html"))
    if not pages:
        report.emit("WARNING", "no HTML pages found in public directory")
    for page in pages:
        relative = page.relative_to(root)
        in_metadata_scope = metadata_pages is None or page in metadata_pages
        if not in_metadata_scope:
            report.emit("INFO", f"non-indexable or undeclared HTML page: {relative}")
        try:
            text = page.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            report.emit("BLOCKER", f"HTML file is not UTF-8: {relative}")
            continue
        parsed = PageParser()
        parsed.feed(text)
        for kind, value in parsed.links:
            target, problem = local_target(root, page, value, expected_origin)
            if problem:
                report.emit("BLOCKER", f"{problem} in {relative}: {value}")
            elif target is not None and not target_exists(root, target, kind):
                report.emit("BLOCKER", f"broken local {kind} in {relative}: {value}")
        if in_metadata_scope:
            required = {"title": parsed.title.strip(), "description": parsed.meta.get("description", ""), "og:title": parsed.meta.get("og:title", ""), "og:description": parsed.meta.get("og:description", ""), "og:image": parsed.meta.get("og:image", ""), "twitter:card": parsed.meta.get("twitter:card", "")}
            metadata_severity = "BLOCKER" if require_metadata else "WARNING"
            for key, value in required.items():
                if not value.strip():
                    report.emit(metadata_severity, f"missing {key} in {relative}")
            if not parsed.canonical:
                report.emit(metadata_severity, f"missing canonical URL in {relative}")
            elif expected_origin and origin(parsed.canonical) != expected_origin:
                report.emit("BLOCKER", f"canonical URL outside configured origin in {relative}: {parsed.canonical}")
        for item in parsed.json_ld:
            try:
                json.loads(item)
            except json.JSONDecodeError as exc:
                report.emit("BLOCKER", f"invalid JSON-LD in {relative}: {exc.msg}")
        if re.search(r"\b(localhost|debugger|console\.log)\b", text, re.IGNORECASE):
            report.emit("WARNING", f"possible development artifact in {relative}")

    sitemap_routes: set[str] = set()
    if not sitemap.is_file():
        report.emit("BLOCKER" if require_sitemap else "WARNING", f"sitemap not found: {args.sitemap_file}")
    else:
        try:
            locations = [node.text.strip() for node in ET.parse(sitemap).iter() if node.tag.endswith("loc") and node.text]
            for location in locations:
                route = normalized_route(urllib.parse.urlsplit(location).path or "/")
                if route is None:
                    report.emit("BLOCKER", f"invalid sitemap route: {location}")
                    continue
                sitemap_routes.add(route)
                if expected_origin and origin(location) != expected_origin:
                    report.emit("BLOCKER", f"sitemap URL outside configured origin: {location}")
                if file_for_route(root, route) is None:
                    report.emit("BLOCKER", f"sitemap URL has no local route: {location}")
            report.emit("INFO", f"checked {len(locations)} sitemap URLs")
        except ET.ParseError as exc:
            report.emit("BLOCKER", f"invalid sitemap XML: {exc}")
    for route in expected_routes:
        if sitemap.is_file() and route not in sitemap_routes:
            report.emit("WARNING", f"expected public route absent from sitemap: {route}")

    if not robots.is_file():
        report.emit("BLOCKER" if require_robots else "WARNING", f"robots file not found: {args.robots_file}")
    elif not re.search(r"(?im)^\s*sitemap\s*:\s*\S+", robots.read_text(encoding="utf-8", errors="replace")):
        report.emit("BLOCKER" if require_robots else "WARNING", "robots.txt has no Sitemap declaration")
    else:
        report.emit("INFO", "robots.txt declares a sitemap")
    return 1 if report.blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
