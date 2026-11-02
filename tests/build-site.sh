#!/usr/bin/env bash
# Builds the fixture site into a Grav install: links the plugin and fixture
# theme, copies the fixture config, and creates one page per pattern example
# plus pages that exercise legacy keys and switches.
#
#   tests/build-site.sh /path/to/grav
set -euo pipefail

GRAV_ROOT="$(cd "${1:?usage: build-site.sh /path/to/grav}" && pwd)"
LIB="$(cd "$(dirname "$0")/.." && pwd)"
P="$LIB/patterns"
F="$LIB/tests/fixtures"
U="$GRAV_ROOT/user"

mkdir -p "$U/plugins" "$U/themes" "$U/config/themes" "$U/config/plugins"
ln -sfn "$LIB" "$U/plugins/component-library"
ln -sfn "$LIB/tests/site/themes/cl-test" "$U/themes/cl-test"
cp "$LIB/tests/site/config/system.yaml" "$LIB/tests/site/config/site.yaml" "$U/config/"
cp "$LIB/tests/site/config/themes/cl-test.yaml" "$U/config/themes/"
cp "$LIB/tests/site/config/plugins/component-library.yaml" "$U/config/plugins/"

rm -rf "$U/pages"
mkdir -p "$U/pages"

page() { # page <folder> <file> <source|-> [image]
    mkdir -p "$U/pages/$1"
    if [ "$3" = "-" ]; then cat > "$U/pages/$1/$2"; else cp "$3" "$U/pages/$1/$2"; fi
    if [ "${4:-}" = "image" ]; then cp "$F/example-photo.jpg" "$U/pages/$1/"; fi
}

page 01.home default.md - <<'EOF'
---
title: Home
author: jd
page_name: Welcome to the River Valley
page_name_subtitle: Four seasons, one river
primary_cta_text: Plan a visit
primary_cta_link: /visit
quick_actions_title: Plan your visit
quick_actions:
  - { label: Things to do, link: /explore, icon: fa-person-hiking }
  - { label: Where to stay, link: /stay }
---
The valley has <div id="map"></div> a map in its content.
EOF

page 02.cta-rows default.md "$P/page/cta-rows/example.md" image
page 03.tiles default.md "$P/page/tiles/example.md" image
page 04.quick-actions default.md "$P/page/quick-actions/example.md"
page 05.page-heading default.md "$P/page/page-heading/example.md"
page 06.header-image default.md "$P/page/header-image/example.md" image
page 07.hero-actions default.md "$P/page/hero-actions/example.md"
page 08.north-landing default.md "$P/theme/schema-graph/example.md"
page 09.boat-launch default.md "$P/page/map-location/example.md"
page 10.embeds default.md "$P/page/embed-block/example.md"
page 11.map map.md "$P/page-type/map-page/example.md"
page 12.jobs jobs.md - <<'EOF'
---
title: Jobs
jobs:
  empty_message: No openings.
---
EOF
page 12.jobs/01.seasonal-tour-guide job.md "$P/page-type/job-listing/example.md"
page 12.jobs/02.closed-position job.md - <<'EOF'
---
title: Closed Position
date: '2025-01-01'
jobtitle: Closed Position
jobdescription: This one has closed.
job:
  valid_through: '2025-02-01'
  remote: true
  apply_url: /jobs/apply
---
EOF
page 13.tour tour.md "$P/page-type/bookable-tour/example.md" image
page 14.landing modular.md "$P/page-type/modular-page/example.md"
page 14.landing/_features section.md - <<'EOF'
---
title: Why visit
tiles:
  - { title: Trails, content: 40 miles of marked trails., tile_width: is-half }
  - { title: Water, content: Paddling and fishing., tile_width: is-half }
info_cta_section:
  - { title: Get the map, button_text: Download, button_link: /map }
---
Sections sit under the page's own heading.
EOF
page 14.landing/_more section.md - <<'EOF'
---
title: More
hide_heading: true
---
A second section with a hidden heading.
EOF

page 15.legacy default.md - <<'EOF'
---
title: 'Legacy keys <b>&</b> escaping'
schema_type: AboutPage
preview_image_selected: /user/pages/15.legacy/example-photo.jpg
info_cta_section:
  - { title: Hidden image row, cta_section_image: '0', cta_section_image_file: example-photo.jpg }
  - { title: Visible image row, cta_section_image: '1', cta_section_image_file: example-photo.jpg }
  - { title: Missing media row, cta_section_image_file: does-not-exist.jpg }
tiles:
  - { title: Hidden tile image, tile_image: '0', tile_image_file: example-photo.jpg }
  - { title: 'Weather', tile_type: weather }
tracking_tags: '<script>/*PAGE-INJECTED*/</script>'
footer_embed: '<script>/*PAGE-INJECTED-FOOTER*/</script>'
---
EOF
cp "$F/example-photo.jpg" "$U/pages/15.legacy/"

page 16.legacy-tour tour.md - <<'EOF'
---
title: Legacy Tour
tourname: River Loop
tourdescription: Three stops in one afternoon.
tourofferprice: '65'
tourofferenddate: '2030-12-31'
tourproductid: P123
tourdayofweek: Saturday
tourtime: '2:00 pm - 5:00 pm'
stops:
  - { description: First Stop }
  - { description: Second Stop }
---
EOF

page 17.legacy-jobs jobs.md - <<'EOF'
---
title: Legacy Jobs
jobdetails:
  - { detailtitle: Driver, content: 'Weekends.', link: /jobs/driver }
---
EOF

page 18.quiet default.md - <<'EOF'
---
title: Quiet Page
head_scripts: false
schema:
  enabled: false
page_scripts: '<script>/*PAGE-SCRIPTS*/</script>'
site_icon:
  user/themes/cl-test/images/uploaded-icon.png: { name: uploaded-icon.png, path: user/themes/cl-test/images/uploaded-icon.png, type: image/png, size: 79 }
site_icon_svg: 'https://icons.example.invalid/page-icon.svg'
---
No tracking, no structured data.
EOF

# Both logo keys set (logo-test.html.twig copies them into theme config): the
# legacy picker value is the editor's choice among the uploads and wins.
page 19.logo logo-test.md - <<'EOF2'
---
title: Logo Precedence
site_logo:
  user/themes/cl-test/images/uploaded-logo.png: { name: uploaded-logo.png, path: user/themes/cl-test/images/uploaded-logo.png, type: image/png, size: 1 }
picked_site_logo_image: picked-logo.png
---
Both logo values are set.
EOF2

# The picked file is gone: the upload is used.
page 20.logo-missing logo-test.md - <<'EOF2'
---
title: Picked Logo Missing
site_logo:
  user/themes/cl-test/images/uploaded-logo.png: { name: uploaded-logo.png, path: user/themes/cl-test/images/uploaded-logo.png, type: image/png, size: 1 }
picked_site_logo_image: deleted-logo.png
---
The picked logo file does not exist.
EOF2

# All three icons uploaded (icons-test.html.twig copies them into theme config).
page 21.icons icons-test.md - <<'EOF2'
---
title: Uploaded Icons
site_icon:
  user/themes/cl-test/images/uploaded-icon.png: { name: uploaded-icon.png, path: user/themes/cl-test/images/uploaded-icon.png, type: image/png, size: 79 }
site_icon_svg:
  user/themes/cl-test/images/uploaded-icon.svg: { name: uploaded-icon.svg, path: user/themes/cl-test/images/uploaded-icon.svg, type: image/svg+xml, size: 111 }
site_icon_touch:
  user/themes/cl-test/images/uploaded-icon.png: { name: uploaded-icon.png, path: user/themes/cl-test/images/uploaded-icon.png, type: image/png, size: 79 }
---
Every icon is uploaded.
EOF2

# The uploaded PNG is gone: the theme's fallback is used.
page 22.icons-missing icons-test.md - <<'EOF2'
---
title: Icon Upload Missing
site_icon:
  user/themes/cl-test/images/deleted-icon.png: { name: deleted-icon.png, path: user/themes/cl-test/images/deleted-icon.png, type: image/png, size: 79 }
---
The uploaded favicon file does not exist.
EOF2

echo "Fixture site built in $GRAV_ROOT/user"
