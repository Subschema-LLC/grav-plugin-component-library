# Grav CMS Component Library

[![Test](https://github.com/Subschema-LLC/grav-plugin-component-library/actions/workflows/test.yml/badge.svg)](https://github.com/Subschema-LLC/grav-plugin-component-library/actions/workflows/test.yml)
[![Grav 1.7 | 2.x](https://img.shields.io/badge/Grav-1.7%20%7C%202.x-2b6cb0)](TESTING.md)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

Reusable, tested patterns for [Grav CMS](https://getgrav.org) themes, pages and
plugins: blueprint fragments, Twig partials, page types, and the Grav 2
practices behind them. Each pattern records the real problems it solves, and
the whole library is machine-readable, so people and AI agents can pick and
apply patterns the same way.

- **26 patterns** across four levels: [theme](docs/CATALOG.md#theme-level),
  [page](docs/CATALOG.md#page-level), [page types](docs/CATALOG.md#page-types)
  and [system](docs/CATALOG.md#system-level).
- **Tested on Grav 2.2.11 and 1.7.53**: every blueprint resolves through
  Grav's own loader and through the API that Admin2 uses, every template
  compiles and renders, and 450+ render checks run in CI on every pull request. See [TESTING.md](TESTING.md).
- **Framework-neutral markup** (`cl-*` BEM classes) with a small optional
  stylesheet, and a `classes` parameter on every partial to add Bulma,
  Bootstrap or Tailwind classes without overriding templates.
- **Drop-in for existing content**: header keys match the ones sites already
  store; where a structure changed, templates still read the older keys.

## Install

As a plugin (recommended), from your Grav root:

```bash
git clone --branch main https://github.com/Subschema-LLC/grav-plugin-component-library user/plugins/component-library
bin/grav clearcache
```

`main` holds released versions; `development` is where changes land first.
The folder must be named `component-library`. The plugin adds the library to
Twig's template paths (after your theme, so your theme can override any
partial), registers the option providers some blueprints use, and loads an
optional stylesheet you can switch off in its settings.

## Use a pattern

Every pattern is a folder under `patterns/<level>/<name>/` with a
`pattern.yaml`, a generated `README.md`, and the files to use.

**0. Find and inspect a pattern** from the command line (or in [docs/CATALOG.md](docs/CATALOG.md)):

```bash
bin/plugin component-library show                  # list all 26 patterns by level
bin/plugin component-library show --search=map     # search by keyword
bin/plugin component-library show page/tiles       # print import@, include, keys & checks (or just: show tiles)
bin/plugin component-library show tiles --copy     # print copy-mode files & snippets (without the plugin)
```

**1. Import its fields** into a page or theme blueprint. `import@` goes on the
field that receives them, as a sibling of `type:`. Several imports on one field
are placed in reverse order (here CTA rows appear above tiles):

```yaml
# user/themes/mytheme/blueprints/default.yaml
extends@: default
form:
  fields:
    tabs:
      fields:
        content_blocks:
          type: tab
          title: Content Blocks
          import@1:
            type: page/tiles/blueprint
            context: 'plugin://component-library/patterns'
          import@2:
            type: page/cta-rows/blueprint
            context: 'plugin://component-library/patterns'
```

**2. Include its partial** in a template, with your framework's classes if you want them:

```twig
{% include 'patterns/page/tiles/tiles.html.twig' with {
    heading_level: 2,
    classes: { button: 'button is-primary' }
} %}
{% include 'patterns/page/cta-rows/cta-rows.html.twig' %}
```

**3. Check it** with the pattern's `verify` list, and lint your theme (defaults to the active theme when no path is given):

```bash
bin/plugin component-library lint
bin/plugin component-library lint user/themes/mytheme
```

Page types (map page, job listing, bookable tour, modular page) also ship a
page blueprint and a template scaffold to copy into your theme; their READMEs
list the steps.

### Without the plugin

Run `bin/plugin component-library show <pattern> --copy` (or read the pattern's
README) to see the exact files and snippets. Copy fragments to
`blueprints/partials/<name>.yaml` (then `context: 'theme://blueprints'`,
`type: partials/<name>`), templates under `templates/patterns/` with the same
paths, and `patterns/_shared/macros.html.twig`. Patterns that list the plugin
under **Requires** explain what to move into your theme class instead.

## See where components are used

In Grav 2's Admin the plugin shows where the library's components are used,
so editors can tell shared components from the theme's own fields and
developers can see what a change will touch:

- **Labels in forms.** A line under each component's fields names it and its
  version, and says when the theme renders it with its own template.
- **A Components panel in the page editor.** A toolbar button, with the number
  of components that have content on the page, opens a list of every
  component the page's template offers: its summary, whether this page fills it
  in (and which fields are filled), which tab it is on, how the theme renders
  it, and a link to its docs.
- **A usage report under Tools → Reports.** Every component in use: its
  summary, the page types and theme settings whose forms include it, the pages
  with content in it (linked to their editor), the theme templates that include
  it and any copies the theme keeps of its templates, ready-to-paste `import@`
  and `include` snippets for unused components, plus the template checks on the
  active theme.

| Labels | Components panel | Usage report |
|---|---|---|
| ![Shared component labels in the page form](docs/images/admin2-field-labels.png) | ![The Components panel in the page editor](docs/images/admin2-components-panel.png) | ![The Component Library usage report](docs/images/admin2-usage-report.png) |

Each can be turned off in the plugin's settings (Grav 2 Admin section). The
same data is available from the command line and to AI agents:

```bash
bin/plugin component-library usage              # the whole site
bin/plugin component-library usage --page=/about
bin/plugin component-library usage --json
```

The plugin's `mcp.yaml` gives the [Grav MCP server](https://learn.getgrav.org/20/advanced/mcp-server)
four tools:
- `component_library_patterns`: list or search patterns by level or keyword
- `component_library_pattern`: inspect one pattern's manifest, `import@` and `include` snippets, keys and checks
- `component_library_usage`: where every pattern is used across the site
- `component_library_page_components`: which patterns a page's template offers and which have content on that page

A component counts as used on a page when one of its fields holds a value
other than its default. Fields are traced through the `cl_pattern` tag every
fragment field carries, so fields a theme defines itself are never counted,
and fragments copied into a theme before 1.3.0 need the tags added. Grav 1.7's
Admin shows none of this; the command works on both. Admin2 has no way for a
plugin to add a column to the Pages list, so the panel and the report are
where per-page usage appears.

## What's inside

| Level | Patterns |
|---|---|
| Theme | site logo, site icons (favicon), author registry, footer columns, head and body-end scripts, data layer, HERE map with conditional loading, Schema.org graph |
| Page | page heading and title tag, header image, hero actions, quick actions, tiles, listing cards, CTA rows, map location, embeds and page scripts |
| Page types | map page, job listing and postings, bookable tour, modular page |
| System | compatibility flag, Admin2-safe plugin forms, dynamic select options, front-end output guards, Twig in content, template hygiene, environments and secrets |

### Quick finder: common needs

| Goal | Patterns to use |
|---|---|
| Landing or content page with cards, call-to-action sections and shortcut links | `page/page-heading`, `page/header-image`, `page/hero-actions`, `page/quick-actions`, `page/tiles`, `page/cta-rows` |
| Product, category or service listing pages whose cards editors add, hide and reorder, with ItemList structured data | `page/listing-cards` (+ `theme/schema-graph` with `main_entity: '#listing'`) |
| Modular page where editors reorder sections | `page-type/modular-page` (built from `page/tiles` and `page/cta-rows`) |
| Site branding (logo and favicon), navigation footer and linked Schema.org JSON-LD | `theme/site-logo`, `theme/site-icons`, `theme/footer-columns`, `theme/schema-graph` |
| Interactive map of places across the site | `theme/map-here` + `page/map-location` on place pages + `page-type/map-page` |
| Analytics, tag manager or third-party embeds without putting scripts in page Markdown | `theme/datalayer`, `theme/head-scripts`, `page/embed-block` |
| Blog or article authors managed in one place | `theme/author-registry` |
| Job board or bookable tour/experience pages with structured data | `page-type/job-listing`, `page-type/bookable-tour` |
| Upgrading a theme or plugin to Grav 2 / Admin2 safely | `system/compatibility-flag`, `system/template-hygiene`, `system/twig-in-content`, `system/dynamic-options`, `system/admin2-plugin-forms` |

The full list with summaries is in [docs/CATALOG.md](docs/CATALOG.md).

## For AI agents

- [`AGENTS.md`](AGENTS.md): how to choose, apply and verify patterns, and the
  Grav rules generated code most often gets wrong.
- [`catalog.json`](catalog.json): every pattern with its import type, include
  path, stored data, problems solved and verification steps.
- [`llms.txt`](llms.txt): an index of raw file links.
- Works alongside the [Grav MCP server](https://learn.getgrav.org/20/advanced/mcp-server):
  browse and inspect patterns with `component_library_patterns` and
  `component_library_pattern`, read a site's blueprints with `get_blueprint`,
  apply patterns, and confirm usage with `component_library_usage`.

## Contributing

Bug reports, fixes and new patterns are welcome. [CONTRIBUTING.md](CONTRIBUTING.md)
covers setting up throwaway Grav installs (`tests/setup-grav.sh`), running the
tests, and what a new pattern needs: real problems in `solves`, a fixture page
and checks, and passing CI on Grav 1.7 and 2.x. The pattern format is in
[docs/PATTERN_SPEC.md](docs/PATTERN_SPEC.md).

Please follow the [code of conduct](CODE_OF_CONDUCT.md), and report security
problems privately as described in [SECURITY.md](SECURITY.md).

## License

MIT. See [LICENSE](LICENSE).
