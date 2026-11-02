#!/usr/bin/env python3
"""
Optional: checks the fixture theme's blueprints through the Grav API, the same
path Admin2 uses. Needs the API plugin (and its Login/Form dependencies), a
user with api access, and an API key for that user:

    CL_API_KEY=grav_... python3 tests/api-check.py http://127.0.0.1:8765

Skips (exit 0) when CL_API_KEY is not set.
"""
import json
import os
import sys
import urllib.request

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8765").rstrip("/") + "/api/v1"
KEY = os.environ.get("CL_API_KEY")
if not KEY:
    print("CL_API_KEY not set; skipping API blueprint checks")
    sys.exit(0)

failures, passes = [], 0


def fetch(path):
    req = urllib.request.Request(BASE + path, headers={"X-API-Key": KEY})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())["data"]


def names(fields, out=None):
    out = {} if out is None else out
    for f in fields or []:
        if isinstance(f, dict):
            if f.get("name"):
                out[f["name"]] = f
            names(f.get("fields"), out)
    return out


EXPECT = {
    "/blueprints/pages/default": ["header.seo_page_title", "header.header_image_file", "header.author", "header.map_marker.latitude",
                                  "header.map_enabled", "header.primary_cta_text", "header.quick_actions", "header.tiles",
                                  "header.info_cta_section", "header.info_cta_section.cta_section_image", "header.tiles.tile_image",
                                  "header.embeds", "header.schema.type", "header.schema.custom_json"],
    "/blueprints/pages/map": ["header.map_page.include_pages", "header.map_markers"],
    "/blueprints/pages/job": ["header.jobtitle", "header.job.salary.min", "header.job.valid_through"],
    "/blueprints/pages/jobs": ["header.jobs.empty_message"],
    "/blueprints/pages/tour": ["header.tour.schedule", "header.tour.price", "header.embeds"],
    "/blueprints/themes/cl-test": ["site_logo", "site_icon", "site_icon_svg", "site_icon_touch", "authors", "footer_columns", "footer_embed", "datalayer.env", "tracking_tags",
                                   "here_map.api_key", "schema_defaults.organization_type"],
    "/blueprints/plugins/component-library": ["enabled", "load_css", "icon_base_class"],
}

for path, expected in EXPECT.items():
    try:
        found = names(fetch(path).get("fields"))
    except Exception as e:  # noqa: BLE001
        failures.append(f"{path}: {e}")
        continue
    for n in expected:
        if n in found:
            passes += 1
        else:
            failures.append(f"{path}: missing {n}")
    phantom = [n for n in found if n == "fields" or n.endswith(".fields")]
    if phantom:
        failures.append(f"{path}: phantom fields {phantom}")
    else:
        passes += 1
    if path == "/blueprints/pages/default":
        # Grav places several import@ on one field in reverse key order (documented in AGENTS.md).
        blocks = next((f for f in fetch(path)["fields"][0]["fields"] if f.get("name") == "blocks"), {})
        order = [f.get("name") for f in blocks.get("fields", []) if f.get("type") == "section"]
        expected = ["header_cta_rows_section", "header_tiles_section", "header_quick_actions_section", "header_hero_actions_section"]
        if order == expected:
            passes += 1
        else:
            failures.append(f"{path}: import@ order changed: {order}")
        opts = [o.get("value") for o in (found.get("header.author", {}).get("options") or [])]
        if opts == ["", "jd", "rk"]:
            passes += 1
        else:
            failures.append(f"{path}: author options from the registry were {opts}")
        cats = [o.get("value") for o in (found.get("header.category", {}).get("options") or [])]
        if cats == ["", "outdoors", "history"]:
            passes += 1
        else:
            failures.append(f"{path}: theme-provided category options were {cats}")


# Where components are used (Admin2 labels, page panel, report) ---------------
def check(ok, message):
    global passes
    if ok:
        passes += 1
    else:
        failures.append(message)


def flat(fields, out=None):
    out = [] if out is None else out
    for f in fields or []:
        if isinstance(f, dict):
            out.append(f)
            flat(f.get("fields"), out)
    return out


def raw(path):
    req = urllib.request.Request(BASE + path, headers={"X-API-Key": KEY})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status, r.headers.get("Content-Type", ""), r.read()


try:
    default = flat(fetch("/blueprints/pages/default")["fields"])
    labels = [f for f in default if str(f.get("name", "")).startswith("cl_component_")]
    ids = sorted(f["name"] for f in labels)
    check(len(labels) == 11 and all(f["type"] == "spacer" for f in labels), f"default blueprint: expected 11 spacer labels, got {ids}")
    pos = [f.get("name") for f in default]
    check(pos.index("cl_component_page_tiles") == pos.index("header_tiles_section") + 1, "the tiles label sits right under its section heading")
    tiles_label = next(f for f in labels if f["name"] == "cl_component_page_tiles")
    check("**Tiles (card grid)**" in tiles_label["text"] and "`page/tiles`" in tiles_label["text"], f"tiles label text: {tiles_label['text']}")
    check(not any("category" in f["name"] for f in labels), "the theme's own field (header.category) gets no label")
    theme_labels = [f["name"] for f in flat(fetch("/blueprints/themes/cl-test")["fields"]) if str(f.get("name", "")).startswith("cl_component_")]
    check("cl_component_theme_site_logo" in theme_labels and "cl_component_theme_site_icons" in theme_labels and "cl_component_theme_footer_columns" in theme_labels, f"theme labels: {theme_labels}")

    page = fetch("/component-library/page?route=/tiles")
    by_id = {c["id"]: c for c in page["components"]}
    check(page["template"] == "default" and len(by_id) == 11, f"/tiles offers 11 components, got {sorted(by_id)}")
    check(by_id.get("page/tiles", {}).get("has_content") is True and by_id["page/tiles"]["tab"] == "Content Blocks", f"page/tiles on /tiles: {by_id.get('page/tiles')}")
    check(bool(by_id.get("page/tiles", {}).get("summary")), "page component includes summary")
    check(by_id.get("page/cta-rows", {}).get("has_content") is False, "cta-rows is empty on /tiles")
    check(by_id.get("page/header-image", {}).get("has_content") is False, "a header image toggle left at its default is not content")
    check("templates/default.html.twig" in by_id["page/tiles"].get("rendered_by", []), "tiles rendered by the fixture's default template")
    badge = fetch("/component-library/page-badge?route=/tiles&lang=en&type=pages")
    check(badge.get("count") == sum(1 for c in page["components"] if c["has_content"]), f"badge count {badge}")
    check(fetch("/component-library/page-badge?route=/no-such-page").get("count") == 0, "badge is 0 for an unknown page")

    catalog_list = fetch("/component-library/patterns?level=page")
    check(catalog_list.get("count") == 8 and all(p["level"] == "page" for p in catalog_list.get("patterns", [])), f"patterns endpoint level=page: {catalog_list.get('count')}")
    tiles_spec = fetch("/component-library/pattern?id=tiles")
    check(tiles_spec.get("id") == "page/tiles" and "copy_mode" in tiles_spec and "partials/tiles" in tiles_spec["copy_mode"]["apply"].get("blueprint", ""), "pattern endpoint resolves short name and includes copy_mode")

    usage = {c["id"]: c for c in fetch("/component-library/usage")["components"]}
    check(any(p["route"] == "/tiles" for p in usage.get("page/tiles", {}).get("pages", [])), "usage lists /tiles under page/tiles")
    check(len(usage.get("page/tiles", {}).get("templates", [])) >= 3, "tiles fields appear in several page types")
    check(usage.get("theme/site-logo", {}).get("theme_settings") is not None, "site-logo is in the theme settings")
    check(not usage.get("page/tiles", {}).get("own_copies"), "no own copy before one exists")

    # A theme copy of a pattern template is reported, identical or customized.
    import pathlib
    lib = pathlib.Path(__file__).resolve().parent.parent
    src = lib / "patterns/page/hero-actions/hero-actions.html.twig"
    copy = lib / "tests/site/themes/cl-test/templates/patterns/page/hero-actions/hero-actions.html.twig"
    try:
        copy.parent.mkdir(parents=True, exist_ok=True)
        copy.write_bytes(src.read_bytes())
        c = {x["id"]: x for x in fetch("/component-library/usage")["components"]}["page/hero-actions"]
        check(c["own_copies"] == [{"file": "templates/patterns/page/hero-actions/hero-actions.html.twig", "identical": True}], f"identical copy: {c['own_copies']}")
        copy.write_bytes(src.read_bytes() + b"{# customized #}\n")
        c = {x["id"]: x for x in fetch("/component-library/usage")["components"]}["page/hero-actions"]
        check(c["own_copies"] and c["own_copies"][0]["identical"] is False, f"customized copy: {c['own_copies']}")
        hero = next(f for f in flat(fetch("/blueprints/pages/default")["fields"]) if f.get("name") == "cl_component_page_hero_actions")
        check("own template" in hero["text"], "the label says when the theme has its own template")
    finally:
        for p in (copy, copy.parent, copy.parent.parent, copy.parent.parent.parent):
            try:
                p.unlink() if p.is_file() else p.rmdir()
            except OSError:
                pass

    panels = fetch("/context-panels")
    panel = next((p for p in panels if p.get("id") == "component-library"), None)
    check(panel is not None and panel.get("contexts") == ["pages"] and panel.get("badgeEndpoint") == "/component-library/page-badge", f"context panel: {panel}")
    reports = fetch("/reports")
    report = next((r for r in reports if r.get("id") == "component-library"), None)
    check(report is not None and report.get("component") == "usage" and report.get("items"), "usage report registered with its component")
    check(report is not None and report.get("lint_total") == 0, f"template checks on the fixture theme: {report and report.get('lint')}")
    for path in ("/gpm/plugins/component-library/panel-script", "/gpm/plugins/component-library/report-script/usage"):
        status, ctype, body = raw(path)
        check(status == 200 and "javascript" in ctype and b"customElements.define" in body, f"{path}: {status} {ctype}")
    tools = fetch("/mcp/tools")
    names_mcp = [t.get("name") for t in (tools.get("tools", []) if isinstance(tools, dict) else tools)]
    check({"component_library_patterns", "component_library_pattern", "component_library_usage", "component_library_page_components"} <= set(names_mcp), f"MCP tools: {names_mcp}")

    # Each feature has a setting that turns it off.
    def patch(body):
        req = urllib.request.Request(BASE + "/config/plugins/component-library", method="PATCH", data=json.dumps(body).encode(),
                                     headers={"X-API-Key": KEY, "Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=30).read()
    patch({"admin2": {"field_labels": False, "page_panel": False, "report": False}})
    try:
        off_labels = [f for f in flat(fetch("/blueprints/pages/default")["fields"]) if str(f.get("name", "")).startswith("cl_component_")]
        check(not off_labels, "field_labels: false removes the labels")
        check(not any(p.get("id") == "component-library" for p in fetch("/context-panels")), "page_panel: false removes the panel")
        check(not any(r.get("id") == "component-library" for r in fetch("/reports")), "report: false removes the report")
    finally:
        patch({"admin2": {"field_labels": True, "page_panel": True, "report": True}})
except Exception as e:  # noqa: BLE001
    failures.append(f"usage checks: {type(e).__name__}: {e}")

print(f"{passes} API checks passed, {len(failures)} failed")
for f in failures:
    print("  FAIL", f)
sys.exit(1 if failures else 0)
