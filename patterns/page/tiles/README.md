<!-- Generated from pattern.yaml by `bin/plugin component-library catalog`. Edit pattern.yaml, not this file. -->
# Tiles (card grid)

`page/tiles` · v1.1.1 · stable · Grav 1.7, 2.0 (tested on 2.2.11, 1.7.53)

An editor-managed grid of cards with widths, icons, markdown text, images, an optional whole-card link and a button, plus a hook for tile types that other templates render.

## Use it when

- A page shows several comparable items (places, services, features) as cards.

## Skip it when

- Each item is a full-width section with one action; use [page/cta-rows](../../page/cta-rows/README.md).
- The cards are just links with a short description; use [page/quick-actions](../../page/quick-actions/README.md).
- Each card stands for a page (a product, category or service) and the list needs child pages or ItemList structured data; use [page/listing-cards](../../page/listing-cards/README.md).

## Requires

- `patterns/_shared/macros.html.twig`

## Apply

**Blueprint**

```yaml
content_blocks:
  type: tab
  title: Content Blocks
  import@:
    type: page/tiles/blueprint
    context: 'plugin://component-library/patterns'
```

**Template**

```twig
{% include 'patterns/page/tiles/tiles.html.twig' with {
    heading_level: 3,
    classes: { button: 'button is-primary' }
} %}
```

## Stored data

Scope: `page.header`

| Key | Type | Notes |
|---|---|---|
| `tiles` | list | `tile_type` content, or a type the theme maps in tile_types; `tile_width` is-one-quarter \| is-one-third \| is-half \| is-two-thirds \| is-full; `title` string; `tile_icon` icon class (Admin2 saves fa-name or fa-brands fa-name); `content` markdown; `tile_image` bool (default on): show the image; `tile_image_file` page media filename; `tile_image_alt` string (empty = decorative); `tile_image_fit` natural \| cover; `card_link` path or URL; `button_text` string; `button_link` path or URL |

## Older keys

- `tiles.*.tile_type = weather`: Rendered by the template you map in tile_types (for example { weather: 'partials/weather-tile.html.twig' } calling the plugin's Twig function). Without a mapping it renders as a content tile.

## Markup classes

`cl-tiles` `cl-tiles__item` `cl-tiles__item--quarter` `cl-tiles__item--third` `cl-tiles__item--half` `cl-tiles__item--two-thirds` `cl-tiles__item--full` `cl-tiles__card` `cl-tiles__card--linked` `cl-tiles__heading` `cl-tiles__icon` `cl-tiles__card-link` `cl-tiles__body` `cl-tiles__media` `cl-tiles__media--cover` `cl-tiles__action` `cl-tiles__button`

Extra classes can be passed for these slots: `root`, `item`, `card`, `heading`, `body`, `media`, `button`.

## Problems this solves

| Problem | Fix | Seen in |
|---|---|---|
| Making a whole card clickable by wrapping it in &lt;a&gt; nested the button link inside another link (invalid HTML) and made screen readers read the whole card as the link name. | The title link is stretched over the card with CSS (.cl-tiles__card--linked); inner links and buttons sit above it and keep working. | community-guide theme, "Full Card Link" |
| Tile headings were always h2, which broke the outline on the home page where tiles sit under an h2 section heading. | heading_level parameter (the home page passes 3). | community-guide theme, v0.2.0 |
| Photos of different shapes made uneven rows, but cropping every image ruined logos. | Per-tile Image Fit (cover crops photos to equal height; natural leaves logos alone). | community-guide theme |
| Width options were Bulma class names written straight into the markup, tying content to one CSS framework. | The stored values stay (no content change), the markup uses neutral cl-tiles__item--half modifiers, and width_classes maps each width to any framework's classes. |  |
| A plugin-rendered tile (weather) was special-cased inside the tile template. | tile_types maps a type to a template, so the tile partial knows nothing about plugins. | community-guide theme, weather tile |
| Admin2's icon picker saves solid icons as a bare fa-name, which renders nothing without a family class. | cl.icon adds the configured family class (default fa-solid). | Admin2 migration |
| Missing media, decorative-image alt text and alt-as-tooltip issues (same as page/cta-rows). | Same guards as page/cta-rows. |  |

## Verify

- [ ] Rendering example.md gives one .cl-tiles__item per non-empty tile with the width modifier.
- [ ] The linked tile has exactly one &lt;a class="cl-tiles__card-link"&gt; and its button is a separate, non-nested link.

## Files

- [`blueprint.yaml`](blueprint.yaml) (blueprint)
- [`tiles.html.twig`](tiles.html.twig) (template)
- [`example.md`](example.md) (example)
