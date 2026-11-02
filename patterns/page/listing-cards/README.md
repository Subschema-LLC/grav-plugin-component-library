<!-- Generated from pattern.yaml by `bin/plugin component-library catalog`. Edit pattern.yaml, not this file. -->
# Listing cards (catalog grid)

`page/listing-cards` · v1.0.0 · stable · Grav 1.7, 2.0 (tested on 2.2.11, 1.7.53)

An editor-managed grid of cards for a listing page (product lines, categories, services), each with an image, short description, description and call to action, optionally standing for a page whose details it borrows, with child pages added automatically and an ItemList for search engines.

## Use it when

- A top-level or category page links to the pages under it (product categories, products, services, programs) as cards, and editors need to add, hide, reorder or retire them without renaming folders.
- The cards should also tell search engines what the page lists (Schema.org ItemList, optionally Product or Service items).

## Skip it when

- The cards are free-form content blocks with icons and mixed widths that do not stand for pages; use [page/tiles](../../page/tiles/README.md).
- The cards are just labelled shortcuts; use [page/quick-actions](../../page/quick-actions/README.md).
- The list must follow dates or another rule with no editorial order (posts, job openings); use a collection or [page-type/job-listing](../../page-type/job-listing/README.md).

## Requires

- `patterns/_shared/macros.html.twig`

## Apply

**Blueprint**

```yaml
listing:
  type: tab
  title: Cards
  import@:
    type: page/listing-cards/blueprint
    context: 'plugin://component-library/patterns'
```

**Template**

```twig
{# In the listing template, under the page content: #}
{% include 'patterns/page/listing-cards/listing-cards.html.twig' with {
    heading_level: 2,
    child_pages: 'fallback',
    children: page.children.published.nonModular,
    page_image_keys: ['card_image'],
    button_text: 'Learn more',
    classes: { button: 'button is-small' }
} %}

{# And in <head>, so the page entity points at the list (theme/schema-graph): #}
{% include 'patterns/theme/schema-graph/schema-graph.html.twig' with {
    main_entity: page.template in ['products', 'category'] ? '#listing' : null
} %}
```

## Stored data

Scope: `page.header`

| Key | Type | Notes |
|---|---|---|
| `listing` | map | `title` string (heading above the cards); `intro` markdown; `columns` 2 \| 3 \| 4; `image_fit` contain \| cover; `button_text` string: call-to-action text for cards without their own; `child_pages` '' (the template's default) \| fallback \| append \| none; `schema_type` ListItem \| Product \| Service |
| `listing_cards` | list | `title` string (empty = the linked page's title); `enabled` bool (default true): false hides the card; `page` page route (optional); `image` page media filename (empty = the linked page's card photo); `image_alt` string (empty = decorative); `short_description` string (empty = the linked page's summary); `description` markdown; `cta_text` string; `cta_link` path or URL (empty = the linked page); `cta_new_tab` bool |

## Markup classes

`cl-listing-cards` `cl-listing-cards__heading` `cl-listing-cards__intro` `cl-listing-cards__grid` `cl-listing-cards__grid--2` `cl-listing-cards__grid--3` `cl-listing-cards__grid--4` `cl-listing-cards__item` `cl-listing-cards__card` `cl-listing-cards__card--linked` `cl-listing-cards__body` `cl-listing-cards__title` `cl-listing-cards__link` `cl-listing-cards__new-tab` `cl-listing-cards__summary` `cl-listing-cards__description` `cl-listing-cards__action` `cl-listing-cards__button` `cl-listing-cards__media` `cl-listing-cards__media--contain` `cl-listing-cards__media--cover` `cl-listing-cards__img`

Extra classes can be passed for these slots: `root`, `heading`, `intro`, `grid`, `item`, `card`, `media`, `body`, `title`, `summary`, `description`, `button`.

## Problems this solves

| Problem | Fix | Seen in |
|---|---|---|
| Category and product listings were built only from child folders, so hiding a product, changing the order or featuring a page from elsewhere meant renaming folders or hand-writing a content collection in front matter. | The cards are a list editors drag, hide and remove. A card can stand for any page; Child Pages adds the rest automatically (only when there are no cards, after the cards, or never). | industrial-equipment theme, product category pages (Gantry migration) |
| Product folders carried over from Gantry had no numeric prefix, so Grav marked them hidden from menus, and a listing that showed only visible pages lost every product. | Child pages are filtered on published and routable, not visible; the theme can pass its own collection as `children`. | industrial-equipment theme, v1.2.2 |
| A card that copied a page's title and summary drifted from the page, and a product taken off the site stayed listed. | A card linked to a page reads that page's title, card photo, summary and address for any empty field, and is hidden once the page is unpublished. A hidden card keeps its page from coming back as a child page. | industrial-equipment theme, product category pages |
| Listing cards printed `summary` from the page header, which on many pages is Grav's summary settings map, and failed with "strip_tags() ... array given". | The header summary is used only when it is text; otherwise the meta description, then the page's own summary. | industrial-equipment theme, v1.2.1 |
| Products photographed on white were cropped by fixed-height card images, while category photos looked uneven without cropping. | Image Fit per listing (whole image or fill), and an image_template hook so a theme can use its own resizing partial. | industrial-equipment theme, v1.1.0 |
| Each card linked to the same page three times (image, title and "Learn More"). The image link was kept out of the tab order, but every card still took two tab stops and screen readers heard each destination twice. | One stretched title link per card; a call to action that goes to the same place is drawn as a button without being a second link. A different destination stays a real link above the card. | industrial-equipment theme, category cards |
| Listing pages were marked CollectionPage in the JSON-LD graph, with nothing saying what they listed. | The same cards are printed as an ItemList (#listing) that the page entity names as its mainEntity; Product items reference the site's Organization as brand and manufacturer. | industrial-equipment theme, theme/schema-graph adoption |

## Verify

- [ ] Rendering example.md with its child pages gives one .cl-listing-cards__item per shown card, in card order, followed by child pages not linked by any card (hidden cards included).
- [ ] A card linked to an unpublished page is not rendered.
- [ ] Each linked card has exactly one link to its page (the title link); a call to action to the same address is a span with aria-hidden="true".
- [ ] A call to action set to open in a new tab has target="_blank" and rel="noopener noreferrer".
- [ ] The ItemList JSON-LD parses, its numberOfItems equals the length of itemListElement, and every element has an absolute URL.
- [ ] The resolved blueprint (GET /api/v1/blueprints/pages/&lt;template&gt;) has header.listing_cards with no field named fields.

## Files

- [`blueprint.yaml`](blueprint.yaml) (blueprint)
- [`listing-cards.html.twig`](listing-cards.html.twig) (template)
- [`example.md`](example.md) (example)
