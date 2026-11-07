# Ostia Management

A Wagtail (Python/Django) website for **Ostia Management**, an independent ISO management-system
certification body. The content follows the structure and substance of a conventional accredited
certification body site; the design, layout and interaction are original.

## Running it

```bash
.venv/Scripts/python.exe manage.py runserver 8010
```

Then open <http://localhost:8010/>. The Wagtail admin is at `/admin/`; create a login with
`manage.py createsuperuser`.

To rebuild the entire site tree from scratch at any point:

```bash
.venv/Scripts/python.exe manage.py import_photos && .venv/Scripts/python.exe manage.py seed_site
```

`seed_site` deletes everything under the Wagtail root and recreates it, so it is the single source
of truth for the launch content. Editors' later changes in the admin would be lost by re-running it.

## How it is put together

```
ostia/settings/      base / dev / production split
core/blocks.py       the StreamField section library (15 block types)
core/models.py       page types, Certificate snippet, SiteSettings
templates/blocks/    one template per block
static/css/site.css  the design system
static/js/site.js    the interaction layer
```

### Page types

| Type | Purpose |
| --- | --- |
| `HomePage` | Built entirely from StreamField sections |
| `StandardPage` | Flexible page for policies, accreditation, process pages |
| `ServiceIndexPage` | Lists its `ServicePage` children with a live category filter |
| `ServicePage` | One certification scheme (code, system name, benefits, accredited flag) |
| `VerifyPage` | Public certificate lookup against the `Certificate` snippet |
| `ContactPage` | Wagtail email form with a configurable field set |

Every page is composed from the same section library, so the whole site is editable without
touching templates. Sections carry a `tone` (cream / white / ink / violet) and, where relevant, a
`style`, which lets an editor vary the rhythm of a page from the admin.

### Design

Paper-white canvas with near-black ink, indigo as the primary and a vivid orange accent, plus a
lavender-to-peach gradient band for testimonials. Bricolage Grotesque for display, Figtree for body.
Photography sits in soft rounded frames overlaid with floating UI badge cards, alongside
hand-drawn marker doodles and dotted-grid texture. Dark rounded slabs carry the service cards, one
highlighted in orange.

Photographs live in `media/original_images`. `import_photos` registers them in the Wagtail image
library; `seed_site` then attaches them by title.

### Interaction

All vanilla JS, no dependencies:

- **Headline reveals** — each heading is split into words that rise behind a mask.
- **Doodles that draw themselves** — SVG arrows animate their own stroke on scroll.
- **Clip-up photography** — framed images wipe in from the bottom edge.
- **Parallax** — photos drift against the scroll while float cards sit still.
- Count-up stats, an animated readiness meter, seamless marquee, magnetic buttons, tabbed panels,
  FAQ accordion, scroll-driven process track, category filtering, scroll progress bar, sticky
  header and a mobile drawer.

Two non-obvious details worth keeping in mind if you extend this:

- A `data-clip` element clips itself to zero height, so IntersectionObserver reports no
  intersection for it and it can never trigger its own reveal. `watch()` therefore observes a
  proxy node (its parent) and marks the clipped child.
- `[data-split] .word` pads its clip box and cancels that padding in the margin. Without it the
  mask is the line box, which is shorter than the glyphs at these tight line-heights, and
  descenders get sliced off.

Accessibility and robustness:

- `prefers-reduced-motion` disables animation throughout.
- Reveal styles are scoped under a `.js` class, so nothing is hidden if scripting is unavailable.
- Interactive controls are real buttons with `aria-expanded` / `aria-selected` / `aria-pressed`.

## Notes

- The dev settings use SQLite, a console email backend and an insecure development key. Production
  settings read `SECRET_KEY` and `ALLOWED_HOSTS` from the environment.
- Policy documents are referenced as download cards; no PDFs are bundled. Uploading a document in
  the admin and selecting it in the block wires up the Open / Download buttons.
- `Certificate` records back the verify page. Five specimens are seeded, including one suspended
  certificate so that status styling can be seen.
- **The marketing numbers and testimonials are placeholders.** The stat tiles (30+, 6, 2, 100%),
  the "346 certified organisations" badge and the three quotes were written to fill the layout.
  Replace them with real figures and real attributed quotes before this goes live — a certification
  body publishing invented performance claims is exactly the kind of thing its own auditors would
  raise.
