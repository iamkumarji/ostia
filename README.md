# Ostia Management

A Wagtail (Python/Django) website for **Ostia Management**, an independent ISO management-system
certification body. The content follows the structure and substance of a conventional accredited
certification body site; the design, layout and interaction are original.

## Running it

The site runs on **PostgreSQL**. Connection details come from the environment, with a `.env`
file at the repository root read on startup (real environment variables win over the file):

```
POSTGRES_DB=ostia
POSTGRES_USER=ostia
POSTGRES_PASSWORD=...
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
WAGTAILADMIN_BASE_URL=http://192.168.1.8:8010
```

`.env` is gitignored — it holds the database password, so it never goes into the repository.

First-time setup on a machine with PostgreSQL installed:

```bash
sudo -u postgres createuser --pwprompt ostia && sudo -u postgres createdb -O ostia ostia
```

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
```

```bash
.venv/bin/python manage.py migrate
```

Then start it, binding to every interface so the site is reachable over the network:

```bash
.venv/bin/python manage.py runserver 0.0.0.0:8010
```

The Wagtail admin is at `/admin/`; create a login with `manage.py createsuperuser`.

To rebuild the entire site tree from scratch at any point:

```bash
.venv/bin/python manage.py import_photos && .venv/bin/python manage.py seed_site
```

`import_photos` reads `media/original_images/*.jpg`, which is gitignored and therefore absent from
a fresh clone. Without it the tree still builds, but the photography slots come out empty; drop the
JPEGs in before seeding to get the images back.

The site expects eleven photographs, named after the title the seeder looks up:

```
audit  consultancy  engineer-lab  factory  office  server
team  team-meeting  training-room  whiteboard  workspace
```

Only `*.jpg` is read — `.png`, `.jpeg` and `.webp` are skipped in silence. Any page that names no
photograph of its own is given one from this set, chosen by a stable hash of its slug, so every
page carries a header image and no two neighbours repeat.

Note that Wagtail stores uploads in `media/original_images/` as well, so each import leaves a copy
of every photo in the folder it just scanned. `import_photos` skips files it has already stored;
without that guard the library doubles on every re-seed.

### Running it as a service

`manage.py runserver` is for development only. On this machine the site runs under Gunicorn as a
systemd unit, `ostia.service`, which is enabled at boot and restarts on failure:

```bash
sudo systemctl status ostia
```

```bash
sudo systemctl restart ostia
```

```bash
journalctl -u ostia -f
```

The unit runs `ostia.settings.production` (`DEBUG` off), so it needs `SECRET_KEY`, `ALLOWED_HOSTS`
and `CSRF_TRUSTED_ORIGINS` in `.env` alongside the database credentials. Add any new hostname or IP
the site is reached on to both `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`, or Django will refuse the
request and forms will return 403.

There is no nginx in front of it. Collected static files are served by WhiteNoise, compressed and
far-future cached, so **run `collectstatic` after changing anything under `static/`** or the change
will not appear:

```bash
DJANGO_SETTINGS_MODULE=ostia.settings.production .venv/bin/python manage.py collectstatic --noinput
```

```bash
sudo systemctl restart ostia
```

`/media/` is deliberately *not* handled by WhiteNoise. Wagtail writes image renditions there the
first time a page renders them, and WhiteNoise only indexes files that exist at startup, so uploads
would 404 until a restart. Django serves that prefix instead — correct, if slower than a real web
server would be. Putting nginx in front is the upgrade path if the site ever faces real traffic.

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

The homepage's "How it works" section uses the process block's cycle diagram style. All of its
wording is edited in the admin, including the labels in the block's "Diagram text" group. The
diagram's shape has six fixed positions, so the admin rejects this style with any other step count.

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

## Contact form and email

Fields are edited on the contact page (form builder) and enquiries are saved under **Forms**. An
editor can put the same form on any page with the **Contact form** section.

Set up email in **Settings > Email settings**: enter the SMTP details and addresses, then enter an
address under "Send a test email to" and save. The result appears on that page. Each enquiry then
sends a notification to the team and, optionally, a confirmation to the visitor.

- An enquiry is saved before anything is sent, so a mail failure cannot lose it. A failure is only
  logged (`core.models` / `core.enquiries`), and the visitor still sees the success message, so
  check **Forms** if mail stops arriving.
- These settings send real email even with the dev settings. Leave them blank locally to send nothing.
- The SMTP password is stored unencrypted in the database, which is excluded from git.
- Spam protection is a honeypot field only. There is no rate limit or CAPTCHA.
- Behind an HTTPS proxy, set the `CSRF_TRUSTED_ORIGINS` and `SECURE_SSL_REDIRECT=true` environment
  variables, or the forms return 403.

Run the tests with `manage.py test core`.

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
