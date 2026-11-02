#!/usr/bin/env python3
"""
Checks `bin/plugin component-library usage --json` on the fixture site (works
on Grav 1.7 too, where there is no API). Reads the JSON on stdin.

    bin/plugin component-library usage --json | python3 tests/usage-check.py
"""
import json
import sys

raw = sys.stdin.read()
try:
    report = json.loads(raw[raw.index("{"):])
except ValueError:
    print("usage: no JSON in the output:", raw[:300])
    sys.exit(1)

failures, passes = [], 0


def check(ok, message):
    global passes
    if ok:
        passes += 1
    else:
        failures.append(message)


by_id = {c["id"]: c for c in report["components"]}
check(report["theme"] == "cl-test", f"theme {report['theme']}")
check(report["pages_scanned"] >= 20, f"pages scanned {report['pages_scanned']}")
check(any(p["route"] == "/tiles" for p in by_id.get("page/tiles", {}).get("pages", [])), "/tiles has tile content")
check(any(p["route"] == "/cta-rows" for p in by_id.get("page/cta-rows", {}).get("pages", [])), "/cta-rows has row content")
check(any(p["route"] == "/gear" for p in by_id.get("page/listing-cards", {}).get("pages", [])), "/gear has listing cards")
check(not any(p["route"] == "/quiet" for c in report["components"] for p in c["pages"] if c["id"] in ("page/tiles", "page/cta-rows")), "/quiet has no blocks")
tabs = {t["template"]: t["tab"] for t in by_id.get("page/tiles", {}).get("templates", [])}
check(tabs.get("default") == "Content Blocks", f"tiles tab on default: {tabs}")
check(by_id.get("theme/site-logo", {}).get("theme_settings") is not None, "site-logo fields in theme settings")
check("templates/partials/base.html.twig" in by_id.get("theme/footer-columns", {}).get("rendered_by", []), "footer rendered by base")
check(bool(by_id.get("page/tiles", {}).get("summary")), "components include their summary")
check(all(c["level"] != "system" for c in report["unused"]), "system patterns are not listed as unused")

print(f"{passes} usage checks passed, {len(failures)} failed")
for f in failures:
    print("  FAIL", f)
sys.exit(1 if failures else 0)
