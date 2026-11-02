<!-- Generated from pattern.yaml by `bin/plugin component-library catalog`. Edit pattern.yaml, not this file. -->
# Site icons

`theme/site-icons` · v1.0.0 · stable · Grav 1.7, 2.0 (tested on 2.2.11, 1.7.53)

Upload fields for the favicon (PNG, plus an optional SVG) and the Apple touch icon, stored outside the theme folder, with a head partial that falls back to the theme's own icons.

## Use it when

- Editors should be able to change the favicon from the theme settings instead of replacing a file on the server.
- The theme is deployed by replacing its folder (a Git theme sync, a GPM update, a reinstall), so an icon swapped inside that folder would be overwritten.

## Skip it when

- The site is an installable web app that needs a manifest with maskable icons and colors; write the manifest in the theme and get the icon URLs from icons.src().

## Apply

**Blueprint**

```yaml
# theme blueprints.yaml, under form.fields:
icons_section:
  type: section
  title: Site Icons
  underline: true
  import@:
    type: theme/site-icons/blueprint
    context: 'plugin://component-library/patterns'
```

**Template**

```twig
{# in <head>; fallback names the icons the theme ships with #}
{% include 'patterns/theme/site-icons/site-icons.html.twig' with {
    fallback: { icon: 'theme://images/favicon.png', svg: 'theme://images/favicon.svg' }
} %}

{# A theme that must keep its favicon when the plugin is not installed: #}
{% set icon_links = include('patterns/theme/site-icons/site-icons.html.twig', { fallback: { icon: 'theme://images/favicon.png' } }, true, true) %}
{% if icon_links|trim is not empty %}{{ icon_links|raw }}{% else %}<link rel="icon" type="image/png" href="{{ url('theme://images/favicon.png')|e }}">{% endif %}

{# Anywhere else that needs an icon URL (a web app manifest, say): #}
{% import 'patterns/theme/site-icons/icons.macros.twig' as icons %}
{% set icon_url = icons.src('site_icon', true) %}
```

## Stored data

Scope: `theme`

| Key | Type | Notes |
|---|---|---|
| `site_icon` | file map | Square PNG favicon. Grav file field value: { 'user/assets/site-icons/favicon.png': { name, path, type, size } } |
| `site_icon_svg` | file map | Optional SVG favicon, stored the same way. |
| `site_icon_touch` | file map | Optional 180 × 180 px PNG for iPhone and iPad home screens, stored the same way. |

## Problems this solves

| Problem | Fix | Seen in |
|---|---|---|
| The favicon was hard-coded to a file in the theme's own folder, and the hosting panel's Git sync replaces that folder on every pull, so a favicon replaced on the server came back as the old one after the next sync. | Uploads are stored in user://assets/site-icons; the theme's bundled icon is only the fallback. | theme deployed through a hosting panel's Git theme sync |
| Editors could not change the favicon from Admin. Each theme kept it somewhere else (its images folder, an assets folder, the site root), so changing it meant finding the file, uploading over it on the server and checking the template. | Theme settings fields, rendered by one partial. | repeated support questions on Grav sites |
| The theme linked only an SVG favicon. Safari and Google Search do not use SVG favicons, so neither showed the site's icon. | A PNG field, which every browser and Google Search accept, with the SVG as an optional extra listed after it. | theme deployed through a hosting panel's Git theme sync |

## Verify

- [ ] Theme settings show Favicon (PNG), Favicon (SVG, optional) and Home-Screen Icon (optional).
- [ ] With nothing uploaded, &lt;head&gt; links the theme's fallback icons, and only those whose files exist.
- [ ] After an upload, the file is in user/assets/site-icons/ and its link points there with ?v=&lt;file size&gt;.
- [ ] The PNG icon link comes before the SVG one.
- [ ] A page's front matter cannot change the icons.

## Files

- [`blueprint.yaml`](blueprint.yaml) (blueprint)
- [`site-icons.html.twig`](site-icons.html.twig) (template)
- [`icons.macros.twig`](icons.macros.twig) (templates)
- [`example.yaml`](example.yaml) (example)
