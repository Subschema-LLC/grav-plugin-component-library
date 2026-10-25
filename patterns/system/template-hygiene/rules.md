# Template rules (checked by `bin/plugin component-library lint`)

| Rule id | Level | What it flags | Fix |
|---|---|---|---|
| `unescaped-header` | warning | `{{ page.header.x }}` or `{{ header.x }}` printed with no filter; safe only while autoescape is on (it is by default, and forced in strict mode) | add `\|e` (or `\|markdown` for markdown fields) |
| `twig-in-html-comment` | error | `{{ }}` or `{% %}` inside `<!-- -->` (Twig still runs there) | use `{# #}` |
| `multiple-extends` | error | more than one `{% extends %}` in a template | keep one, as the first tag |
| `nested-comment` | error | `{#` inside a `{# ... #}` comment (Twig comments do not nest) | write notes with `--` |
| `theme-var-raw` | error | `theme_var(...)` value printed with `\|raw` (page front matter can override theme_var) | read trusted HTML with `grav.config.get('theme.key')` |
| `blank-without-rel` | warning | `target="_blank"` with no `rel="noopener` on the same tag | add `rel="noopener noreferrer"` or use `cl.link_attrs` |
| `json-without-hex-tag` | warning | `json_encode` (no flags, or flags without bit 1) inside a `<script>` element | `json_encode(15)` or `json_encode(321)` |
| `twig1-syntax` | error | `{% filter %}`, `{% spaceless %}`, `{% for x in y if z %}` | `{% apply %}`, the `spaceless` filter, `{% if %}` inside the loop |
| `media-url-true` | warning | `page.media[...].url(true)`: looks absolute but is relative (the argument means "reset") | `url(page.media[file].url, true)` |
| `lazy-header-image` | warning | `loading('lazy')` on a header or hero image | `loading('eager').fetchpriority('high')` |
| `dropdown-always-open` | warning | `is-active` (or a `current_page` variable containing `is-active`) placed on a Bulma `.has-dropdown` container, forcing `.navbar-dropdown` to stay open on active pages | put `is-selected` on `.has-dropdown` and `is-active` on the inner `.navbar-link` |

The checks are line-based heuristics: they catch the problems this library has
actually hit, not every possible mistake. A rule can be silenced for one line
with a trailing `{# lint-ignore: rule-id #}`.
