<!-- Generated from pattern.yaml by `bin/plugin component-library catalog`. Edit pattern.yaml, not this file. -->
# Twig template hygiene for Grav 2

`system/template-hygiene` · v1.0.0 · stable · Grav 1.7, 2.0 (tested on 2.2.11, 1.7.53)

The template rules every pattern here follows, checkable on any theme with `bin/plugin component-library lint <path>`.

## Use it when

- Writing or reviewing any theme or plugin template.
- Moving a theme to Grav 2 (Twig 3, twig3_compat off).

## Requires

- the component-library plugin (or copy the files; see the main README)

## Apply

**PHP or shell**

```bash
# From the Grav root, against a theme or plugin folder:
bin/plugin component-library lint user/themes/mytheme
```

## Problems this solves

| Problem | Fix | Seen in |
|---|---|---|
| Page titles were printed as {{ page.header.title }} with no filter, flagged by code scanning in two templates. Grav's autoescape covered them, but only for as long as autoescape stays on (twig2_compat turns it off). | Escape every stored value explicitly with \|e; \|markdown for markdown fields; \|raw only for documented trusted-HTML fields. (lint rule unescaped-header, a warning) | community-guide theme, code-scanning fixes |
| A logout link "commented out" with &lt;!-- --&gt; still rendered a security nonce into every page, because Twig runs inside HTML comments. | Comment out Twig with {# | community-guide theme, v0.2.0 |
| A template had two {% extends %} tags and failed with "Multiple extends tags are forbidden", taking the password-reset page down. | One extends per template, as its first tag. (lint rule multiple-extends) | community-guide theme, v0.2.0 |
| A doc comment containing {# ... | Twig comments do not nest; write notes inside comments with "--" instead. (lint rule nested-comment) | this library's own first draft |
| Trusted-HTML settings were read with theme_var(), which lets page front matter override them, then printed with \|raw. | Read trusted fields with grav.config.get('theme.&lt;key&gt;'). (lint rule theme-var-raw) | library review of the community-guide footer and head templates |
| Links opening a new tab lacked rel="noopener noreferrer". (lint rule blank-without-rel) | Use cl.link_attrs or add the rel attribute. | community-guide theme |
| JSON inside &lt;script&gt; tags was printed with plain json_encode, so a "&lt;/script&gt;" in any value could end the tag. | json_encode with JSON_HEX_TAG (any flags value with bit 1 set, such as 15 or 321). (lint rule json-without-hex-tag) | Gantry schema particle |
| Templates used Twig 1/2 syntax removed in Twig 3, such as {% filter %}, {% spaceless %} or "for ... if", and only worked with twig3_compat on. | {% apply %}, the spaceless filter, and an {% if %} inside the loop; test with twig3_compat: false. (lint rule twig1-syntax) | Grav 2 migration |
| Structured-data image URLs were built with page.media[file].url(true), expecting an absolute URL; media url()'s argument means "reset", so the JSON-LD carried relative paths. | url(page.media[file].url, true) adds the scheme and host. (lint rule media-url-true) | community-guide theme, Schema.org partial (found while testing this library on Grav 2.2.11) |
| Adding current_page ('is-active is-selected') to a Bulma .navbar-item.has-dropdown wrapper kept that section's flyout menu permanently open on the section page and all its child pages, so the dropdown could not be closed. | Put is-selected on .navbar-item.has-dropdown and is-active on the inner .navbar-link. (lint rule dropdown-always-open) | Bulma theme navigation partial |

## Verify

- [ ] bin/plugin component-library lint &lt;theme folder&gt; reports no errors.
- [ ] The theme renders with system.strict_mode.twig3_compat false.

## Files

- [`rules.md`](rules.md) (snippets)
