#!/usr/bin/env python3
"""
Render checks for the fixture site (tests/build-site.sh), run against a live
Grav server. Standard library only.

    python3 tests/check.py http://127.0.0.1:8765
"""
import json
import re
import sys
import urllib.request
import urllib.error

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8765").rstrip("/")
failures = []
passes = 0


def get(route):
    try:
        with urllib.request.urlopen(BASE + route, timeout=30) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")


def check(route, cond, msg):
    global passes
    if cond:
        passes += 1
    else:
        failures.append(f"{route}: {msg}")


def count(html, pattern):
    return len(re.findall(pattern, html))


def jsonld(html):
    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
    return [json.loads(b) for b in blocks]


def graph(html):
    for d in jsonld(html):
        if "@graph" in d:
            return d["@graph"]
    return None


def common(route, html, status):
    check(route, status == 200, f"HTTP {status}")
    check(route, "Twig\\Error" not in html and "Whoops" not in html and "Fatal error" not in html, "error page or Twig error")
    check(route, not re.search(r"\{\{|\{%|#\}", re.sub(r"<script.*?</script>", "", html, flags=re.S)), "raw Twig leaked into the page")
    check(route, "Twig sandbox blocked" not in html, "sandbox blocked an expression")
    for tag in re.findall(r"<a\b[^>]*>", html):
        if 'target="_blank"' in tag:
            check(route, "noopener" in tag, f"_blank link without noopener: {tag}")
    for d in re.findall(r'<script type="application/(?:ld\+)?json"[^>]*>(.*?)</script>', html, re.S):
        try:
            json.loads(d)
            ok = True
        except ValueError:
            ok = False
        check(route, ok, "a JSON script block does not parse")
    check(route, "/*PAGE-INJECTED" not in html, "page front matter injected a trusted-HTML theme setting")


pages = {}
for route in ["/", "/cta-rows", "/tiles", "/quick-actions", "/page-heading", "/header-image", "/hero-actions",
              "/north-landing", "/boat-launch", "/embeds", "/map", "/jobs", "/jobs/seasonal-tour-guide",
              "/jobs/closed-position", "/tour", "/landing", "/legacy", "/legacy-tour", "/legacy-jobs", "/quiet", "/logo", "/logo-missing",
              "/icons", "/icons-missing", "/gear", "/gear-catalog"]:
    status, html = get(route)
    pages[route] = html
    common(route, html, status)

# Theme level -----------------------------------------------------------------
h = pages["/"]
check("/", "component-library.css" in h.split("</head>")[0], "plugin stylesheet loads")
check("/", count(h, r'<script type="application/json" id="cl-datalayer-config">') == 1, "datalayer config block")
check("/", '"app_env":"development"' in h and '"collection_method":"tms-lite"' in h, "datalayer values from theme config")
check("/", "datalayer.js" in h.split("</head>")[0], "datalayer.js loads in the head")
check("/", h.split("</head>")[0].count("/*HEAD-TAG*/") == 1, "head tracking snippet once, in <head>")
check("/", h.count("/*BODY-END*/") == 1, "body-end snippet once")
check("/", 'class="cl-site-logo"' in h and "cl-site-logo__text" in h, "logo partial falls back to the site title")
check("/", "River &amp; Trails Association" in h, "site title escaped once (no &amp;amp;)")
check("/", "&amp;amp;" not in h, "double escaping")
check("/", count(h, r'class="cl-footer__column"') == 2 and "footer-embed-fixture" in h, "two link columns plus the embed column")
check("/", "/missing-label" not in h, "footer link without a label is skipped")
check("/", "An independent community resource." in h and re.search(r"© 20\d\d River &amp; Trails", h), "footer note tokens replaced")
check("/", 'aria-label="Facebook"' in h and "fa-brands fa-facebook" in h and ">Mastodon<" in h, "social links (icon and text fallback)")
check("/", "mapsjs-core.js" in h and 'id="cl-map-config"' in h, "map loader triggered by id=\"map\" in content")
check("/", '"apiKey":"test-browser-key"' in h, "map config carries the API key")
g = graph(h)
check("/", g is not None and count(h, r'"@graph"') == 1, "exactly one @graph")
if g:
    types = [n["@type"] for n in g]
    check("/", types[:3] == ["NGO", "WebSite", "BreadcrumbList"], f"graph starts with publisher, site, breadcrumbs: {types}")
    webpage = g[-1]
    check("/", webpage.get("about", {}).get("name") == "The River Valley", "home page about Place")
    check("/", g[1].get("description") == "Fixture site for the Grav CMS Component Library.", "WebSite carries the site description")
check("/", "cl-author" in h and "Jane Doe" in h and 'rel="author"' in h, "author card for author: jd")
check("/", 'aria-label="example.org"' not in h and 'aria-label="Jane Doe on example.org"' in h, "social link label fallback names the host")
check("/", count(h, r'<h1\b') == 1, "exactly one h1")
check("/", "<title>River &amp; Trails Association</title>" in h, "home title is the site title only")

q = pages["/quiet"]
check("/quiet", "/*HEAD-TAG*/" not in q and "/*BODY-END*/" not in q, "head_scripts: false turns snippets off")
check("/quiet", "application/ld+json" not in q, "schema.enabled false removes structured data")
check("/quiet", "/*PAGE-SCRIPTS*/" in q, "page_scripts render before </body>")
check("/quiet", "mapsjs-core.js" not in q, "no map scripts on a page without a map")

lg = pages["/logo"]
check("/logo", "assets/images/global/picked-logo.png" in lg and "uploaded-logo.png" not in lg, "picked_site_logo_image wins over site_logo")
lgo = (graph(lg) or [{}])[0].get("logo", {}).get("url", "")
check("/logo", lgo.startswith("http") and lgo.endswith("/assets/images/global/picked-logo.png"), f"schema logo uses the picked logo, absolute: {lgo}")
lm = pages["/logo-missing"]
check("/logo-missing", "uploaded-logo.png" in lm and "deleted-logo.png" not in lm, "a missing picked file falls back to site_logo")
lmo = (graph(lm) or [{}])[0].get("logo", {}).get("url", "")
check("/logo-missing", lmo.startswith("http") and lmo.endswith("/images/uploaded-logo.png"), f"schema logo falls back to the upload: {lmo}")

hd = h.split("</head>")[0]
check("/", re.search(r'<link rel="icon" type="image/png" href="[^"]*/images/fallback-icon\.png">', hd), "fallback PNG icon in <head>")
check("/", re.search(r'<link rel="icon" type="image/svg\+xml" href="[^"]*/images/fallback-icon\.svg">', hd), "fallback SVG icon in <head>")
check("/", 0 <= hd.find("fallback-icon.png") < hd.find("fallback-icon.svg"), "PNG icon listed before the SVG icon")
check("/", "missing-touch.png" not in h and 'rel="apple-touch-icon"' not in h, "a fallback whose file is missing is left out")
ic = pages["/icons"].split("</head>")[0]
check("/icons", re.search(r'<link rel="icon" type="image/png" href="[^"]*/images/uploaded-icon\.png\?v=79">', ic), "uploaded PNG icon with ?v=<size>")
check("/icons", re.search(r'<link rel="icon" type="image/svg\+xml" href="[^"]*/images/uploaded-icon\.svg\?v=111">', ic), "uploaded SVG icon with ?v=<size>")
check("/icons", re.search(r'<link rel="apple-touch-icon" href="[^"]*/images/uploaded-icon\.png\?v=79">', ic), "uploaded touch icon")
check("/icons", "fallback-icon" not in pages["/icons"] and count(ic, r'<link rel="icon"') == 2, "uploads replace the fallbacks, one link each")
im = pages["/icons-missing"]
check("/icons-missing", "deleted-icon.png" not in im and "/images/fallback-icon.png" in im, "a missing upload falls back to the theme's icon")
check("/quiet", "uploaded-icon" not in q and "icons.example.invalid" not in q and "/images/fallback-icon.png" in q, "page front matter cannot change the icons")

# Page level ------------------------------------------------------------------
c = pages["/cta-rows"]
check("/cta-rows", count(c, r'class="cl-cta-rows__row[ "]') == 3, "three CTA rows")
check("/cta-rows", 'alt="A wooden boardwalk crossing a marsh at sunrise"' in c, "alt text")
check("/cta-rows", 'alt=""' in c, "decorative image keeps empty alt")
check("/cta-rows", 'title="A wooden boardwalk' not in c, "alt text is not repeated as a title")
check("/cta-rows", 'loading="lazy"' in c, "row images lazy-load")
check("/cta-rows", "btn btn-primary" in c, "classes slot applied")

t = pages["/tiles"]
check("/tiles", count(t, r'class="cl-tiles__item ') == 4, "four tiles")
check("/tiles", count(t, r'cl-tiles__item--third') == 3 and "cl-tiles__item--full" in t, "width modifiers")
check("/tiles", count(t, r'<a class="cl-tiles__card-link"') == 1, "one whole-card link")
check("/tiles", '<i class="fa-solid fa-water' in t, "bare Admin2 icon gets the family class")
check("/tiles", '<i class="fa-brands fa-pagelines' in t and '<i class="fa fa-tree' in t, "icons with a family keep it")
check("/tiles", "Weather tile for Weather (h2)" in t, "custom tile type rendered by the mapped template")
check("/tiles", "cl-tiles__media--cover" in t, "cover image fit")

qa = pages["/quick-actions"]
check("/quick-actions", count(qa, r'class="cl-quick-actions__item"') == 3, "incomplete shortcut skipped")
check("/quick-actions", 'aria-labelledby="quick-actions-title"' in qa and "cl-quick-actions__grid--4" in qa, "nav label and columns")

ph = pages["/page-heading"]
check("/page-heading", "<title>Visiting the River Valley — Maps, Lodging &amp; Events | River &amp; Trails Association</title>" in ph, "SEO title tag")
check("/page-heading", re.search(r'<h1 class="cl-page-heading__title">Welcome to the River Valley</h1>', ph), "visible H1 from page_name")
check("/page-heading", '<p class="cl-page-heading__subtitle">' in ph, "subtitle is a paragraph")

hi = pages["/header-image"]
img = re.search(r'<img[^>]*cl-header-image__img[^>]*>', hi)
check("/header-image", img is not None, "header image rendered")
if img:
    tag = img.group(0)
    check("/header-image", 'loading="eager"' in tag and 'fetchpriority="high"' in tag, f"eager + high priority: {tag}")
    check("/header-image", "srcset=" in tag and "sizes=" in tag, "responsive srcset")

ha = pages["/hero-actions"]
check("/hero-actions", count(ha, r'cl-hero-actions__button--') == 1, "only the complete action renders")

e = pages["/embeds"]
check("/embeds", count(e, r"<iframe ") == 2, "http embed skipped, two iframes")
check("/embeds", all('title="' in f and 'loading="lazy"' in f for f in re.findall(r"<iframe [^>]*>", e)), "iframes titled and lazy")
check("/embeds", 'height="900"' in e and "cl-embeds__frame--16x9" in e, "fixed and ratio shapes")
check("/embeds", 'style="' not in "".join(re.findall(r'<div class="cl-embeds__frame[^>]*>', e)), "no inline styles")

nl = pages["/north-landing"]
g = graph(nl) or []
place = next((n for n in g if n.get("@id", "").endswith("#place")), None)
check("/north-landing", place is not None and place["@type"] == "Park", "Place entity typed Park")
if place:
    check("/north-landing", place.get("address", {}).get("addressLocality") == "Riverton", "address default from theme settings")
check("/north-landing", "</script><b>" not in nl, "JSON_HEX_TAG keeps </script> out of the JSON-LD")
hg = graph(pages["/header-image"]) or []
check("/header-image", hg and str(hg[-1].get("image", "")).startswith("http"), "page image in JSON-LD is absolute")


def listing(html):
    """The listing-cards block from its opening tag to the end of its grid, or ''."""
    m = re.search(r'<(?:section|div) class="cl-listing-cards[ "].*?</ul>', html, re.S)
    return m.group(0) if m else ""


def item_list(html):
    return next((d for d in jsonld(html) if d.get("@type") == "ItemList"), None)


g = listing(pages["/gear"])
cards = re.findall(r'<li class="cl-listing-cards__item">(.*?)</li>', g, re.S)
titles = [re.sub(r"<[^>]+>", "", re.search(r'class="cl-listing-cards__title">(.*?)</h\d>', c, re.S).group(1)).strip() for c in cards]
check("/gear", titles == ["Canoes", "Guided float trip (opens in a new tab)", "Kayaks"], f"cards in order, then child pages no card links: {titles}")
check("/gear", "Paddleboards" not in g and "Retired Boat" not in g, "a hidden card and a card for an unpublished page do not render, nor come back as child pages")
check("/gear", '<section class="cl-listing-cards" aria-labelledby="listing-heading">' in g and '<h2 id="listing-heading"' in g, "titled listing is a labelled section")
check("/gear", count(g, r'<h3 class="cl-listing-cards__title">') == 3, "card titles one level below the listing heading")
check("/gear", "Reserve a day ahead" in g and "<strong>9 am</strong>" in g, "intro and description markdown")
check("/gear", cards and cards[0].count('href="/gear/canoes"') == 1, "a linked card links to its page once")
check("/gear", cards and 'class="cl-listing-cards__button btn btn-sm" href="/reserve?boat=canoe&amp;people=2"' in cards[0], "a call to action elsewhere stays a real, escaped link")
check("/gear", cards and 'src="/user/pages/23.gear/01.canoes/example-photo.jpg"' in cards[0] and 'alt=""' in cards[0], "linked card uses its page's card_image, decorative alt")
check("/gear", len(cards) > 1 and 'target="_blank" rel="noopener noreferrer"' in cards[1] and 'alt="Two canoes on a calm river at sunrise"' in cards[1], "own link opens in a new tab with its own image")
check("/gear", len(cards) > 1 and '<span class="cl-listing-cards__button btn btn-sm" aria-hidden="true">Book a trip</span>' in cards[1], "a button to the title's address is not a second link")
check("/gear", len(cards) > 2 and "Sit-on-top kayaks for one paddler." in cards[2] and "See details" in cards[2], "child page: meta description (summary settings map skipped), default call to action")
check("/gear", "cl-listing-cards__grid--3" in g and "cl-listing-cards__media--contain" in g and "srcset=" in g, "columns, image fit and responsive images")
il = item_list(pages["/gear"]) or {}
els = il.get("itemListElement", [])
check("/gear", il.get("@id", "").endswith("/gear#listing") and il.get("mainEntityOfPage", {}).get("@id", "").endswith("/gear#webpage"), "ItemList @id and link to the page entity")
check("/gear", il.get("numberOfItems") == len(els) == 3 and [e.get("position") for e in els] == [1, 2, 3], "ItemList counts and positions")
check("/gear", all(e.get("@type") == "ListItem" and str(e.get("url", "")).startswith("http") for e in els), "ListItems with absolute URLs")
check("/gear", els and str(els[0].get("image", "")).startswith("http") and els[0].get("name") == "Canoes", "linked card's name and absolute image")

gc = listing(pages["/gear-catalog"])
check("/gear-catalog", gc.startswith('<div class="cl-listing-cards">') and count(gc, r'<h2 class="cl-listing-cards__title">') == 2, "no cards: child pages (fallback) as h2 cards in an untitled block")
check("/gear-catalog", "cl-listing-cards__grid--4" in gc and "cl-listing-cards__media--cover" in gc, "four columns, cover fit")
check("/gear-catalog", "packs to &lt;b&gt;two&lt;/b&gt; pounds" in gc, "a text summary from the page header is escaped")
il = item_list(pages["/gear-catalog"]) or {}
prods = [e.get("item", {}) for e in il.get("itemListElement", [])]
check("/gear-catalog", len(prods) == 2 and all(p.get("@type") == "Product" and p.get("brand", {}).get("@id", "").endswith("/#organization") for p in prods), "Product items branded by the organization")
check("/gear-catalog", il.get("name") == "Camp <gear> & stoves" and all("<" not in p.get("description", "") for p in prods), "ItemList name from the page title; descriptions without tags")

# Page types ------------------------------------------------------------------
m = pages["/map"]
markers = json.loads(re.search(r'<script type="application/json" id="cl-map-markers">(.*?)</script>', m, re.S).group(1))
check("/map", isinstance(markers, list), "markers JSON is an array")
items = count(m, r'class="cl-map-page__place"')
check("/map", len(markers) == items, f"{len(markers)} markers vs {items} list items")
idx = [int(i) for i in re.findall(r'data-marker-index="(\d+)"', m)]
check("/map", idx == list(range(len(idx))), "data-marker-index is sequential")
check("/map", any(p["url"].endswith("/north-landing") for p in markers) and any(p["url"].endswith("/boat-launch") for p in markers), "pages with map_marker are pinned")
check("/map", [p["title"] for p in markers] == sorted([p["title"] for p in markers], key=str.lower), "markers sorted by title")
il = [d for d in jsonld(m) if d.get("@type") == "ItemList"]
check("/map", len(il) == 1 and il[0]["numberOfItems"] == len(markers), "ItemList matches the list")
mg = graph(m) or []
check("/map", mg and mg[-1].get("mainEntity", {}).get("@id", "").endswith("/map#places") and il and il[0]["@id"] == mg[-1]["mainEntity"]["@id"], "main_entity links the page to its ItemList")
check("/map", 'data-datalayer-event="map_view"' in m and "mapsjs-core.js" in m, "map events and scripts")

j = pages["/jobs"]
check("/jobs", "Seasonal Tour Guide" in j and "Closed Position" not in j, "closed posting is not listed")
jp = pages["/jobs/seasonal-tour-guide"]
post = next((d for d in jsonld(jp) if d.get("@type") == "JobPosting"), None)
check("/jobs/seasonal-tour-guide", post is not None, "JobPosting JSON-LD")
if post:
    for k in ["title", "description", "datePosted", "hiringOrganization", "jobLocation", "validThrough", "baseSalary", "employmentType"]:
        check("/jobs/seasonal-tour-guide", k in post, f"JobPosting.{k}")
    check("/jobs/seasonal-tour-guide", post["baseSalary"]["value"].get("minValue") == 18, "salary range")
check("/jobs/seasonal-tour-guide", "$18–$22.50 per hour" in jp, "pay formatting")
jc = pages["/jobs/closed-position"]
check("/jobs/closed-position", "This position is closed." in jc and "Apply for this job" not in jc, "closed notice replaces apply")
cp = next((d for d in jsonld(jc) if d.get("@type") == "JobPosting"), {})
check("/jobs/closed-position", cp.get("jobLocationType") == "TELECOMMUTE", "remote posting")

tr = pages["/tour"]
trip = next((d for d in jsonld(tr) if d.get("@type") == "TouristTrip"), None)
check("/tour", trip is not None, "TouristTrip JSON-LD")
if trip:
    check("/tour", trip["offers"]["price"] == "79.00" and trip["offers"]["availability"].endswith("LimitedAvailability"), "offer")
    check("/tour", trip["itinerary"]["numberOfItems"] == 3, "itinerary of three stops")
    check("/tour", trip.get("duration") == "PT210M", "duration")
    check("/tour", trip.get("image", "").startswith("http"), f"absolute image URL: {trip.get('image')}")
check("/tour", "Saturday, <time>1:00 pm</time>–<time>4:30 pm</time>" in tr, "schedule formatting")
check("/tour", "3 hr 30 min" in tr, "duration formatting")
check("/tour", "Book this tour" in tr and "booking.example.com" in tr, "booking embed")

lt = pages["/legacy-tour"]
lt_trip = next((d for d in jsonld(lt) if d.get("@type") == "TouristTrip"), {})
check("/legacy-tour", lt_trip.get("name") == "River Loop" and lt_trip.get("offers", {}).get("price") == "65.00", "legacy tour keys")
check("/legacy-tour", "Saturday, 2:00 pm - 5:00 pm" in lt and "Second Stop" in lt, "legacy schedule and stops")

lj = pages["/legacy-jobs"]
check("/legacy-jobs", "Driver" in lj and 'href="/jobs/driver"' in lj, "legacy jobdetails list")

ld = pages["/landing"]
check("/landing", 'id="features"' in ld and 'id="more"' in ld, "module ids from slugs")
check("/landing", count(ld, r'<h2 class="cl-section__heading">') == 1, "hidden heading respected")
check("/landing", count(ld, r'<h3 class="cl-tiles__heading">') == 2 and count(ld, r'<h3 class="cl-cta-rows__heading">') == 1, "blocks in modules use h3")

lg = pages["/legacy"]
check("/legacy", count(lg, r'cl-cta-rows__media') == 1, "legacy image toggle respected, missing media skipped")
check("/legacy", "Legacy keys &lt;b&gt;&amp;&lt;/b&gt; escaping" in lg, "title escaped")
check("/legacy", "cl-tiles__media" not in lg, "legacy tile image toggle respected")
lgg = graph(lg) or []
check("/legacy", lgg and lgg[-1].get("@type") == "AboutPage", "legacy schema_type read")
check("/legacy", lgg and str(lgg[-1].get("image", "")).startswith("http") and "example-photo.jpg" in str(lgg[-1].get("image")), "preview_image_selected used as the absolute page image")

# The optional stylesheet must only style the library's own classes, because it
# loads on every page of any site that installs the plugin.
import os
css = open(os.path.join(os.path.dirname(__file__), "..", "assets", "component-library.css")).read()
css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
for sel in re.findall(r"([^{}]+)\{", css):
    sel = sel.strip()
    if sel.startswith("@") or not sel:
        continue
    for part in sel.split(","):
        part = part.strip()
        check("component-library.css", ".cl-" in part, f"selector not scoped to .cl-*: {part}")

print(f"{passes} checks passed, {len(failures)} failed")
for f in failures:
    print("  FAIL", f)
sys.exit(1 if failures else 0)
