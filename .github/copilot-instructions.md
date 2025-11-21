# Copilot / AI Agent Guide — Zwiggy-Food-Delivery

This file gives focused, actionable guidance so an AI coding agent can be productive quickly in this Django-based project.

Overview
- App type: monolithic Django app serving server-rendered templates (no frontend build found in repo). Main Django app is `main` under `zwiggy/main/`.
- DB: SQLite (see `zwiggy/zwiggy/settings.py`). Media served from `media/`, static files under `main/static/`.

Quick dev tasks
- Install dependencies (virtualenv recommended). Example (PowerShell):
  - `python -m venv .venv`
  - `.\.venv\Scripts\Activate.ps1; pip install django`
- Run migrations: `python manage.py migrate`
- Start dev server: `python manage.py runserver`

Project layout & important files
- `zwiggy/zwiggy/settings.py`: project settings. Note `DEBUG = True` and SQLite DB path `BASE_DIR / 'db.sqlite3'`.
- `zwiggy/manage.py`: standard Django CLI entrypoint.
- `main/models.py`: core data model — `Restaurant`, `MenuItem`, `CartItem`, `Order`, `OrderItem`.
  - `CartItem` uses `unique_together = ('user', 'item')` and `total_price()` helper.
  - `Order` / `OrderItem` model pair are used during checkout in `views.checkout`.
- `main/views.py`: contains most business logic (authentication flows, cart merge logic, checkout). Key patterns:
  - Guest carts are stored in the session as `request.session['cart']` with string keys (menu item id) and integer quantities.
  - On login, `_merge_session_cart_to_db` transfers session cart into `CartItem` rows for the authenticated `User`.
  - `add_to_cart` and `remove_from_cart` support both session and DB paths depending on `request.user.is_authenticated`.
  - `checkout` constructs an `Order` and `OrderItem`s directly from `CartItem` rows and then deletes the `CartItem`s.
- `main/urls.py`: URL surface. Important endpoints: `'' (home)`, `/restaurants/`, `/cart/`, `/checkout/`, `/order-success/<id>/`.
- `main/templates/main/`: server-rendered templates. Use these when making view or template changes.

Conventions & patterns to follow
- Use ORM-level operations; views are currently synchronous and simple — continue with standard Django view patterns.
- Session cart keys are strings. When reading/writing session cart, convert ids using `str()` or `int()` consistently (see `views._merge_session_cart_to_db` and `view_cart`).
- When altering cart-related behavior, update both session and DB flows and the merge helper to keep behavior consistent.
- Image fields: `MenuItem.image` and `Restaurant.image` may be `None`; guard against `None` when rendering (code uses `.image.url if mi.image else None`).

Developer workflows & commands
- Common commands (PowerShell):
  - `python manage.py makemigrations` — create migrations
  - `python manage.py migrate` — apply migrations
  - `python manage.py createsuperuser` — create admin
  - `python manage.py runserver` — run local server
- No test framework or `requirements.txt` detected in repository — assume plain Django install. Add `requirements.txt` if you add new deps.

Integration points & gotchas
- No external services or third-party APIs are present. All state is local (SQLite, filesystem for media).
- Static and media config in `settings.py`: static files resolved from `main/static/`, and media directory is the repo `media/` (templates and views expect these paths).
- Authentication uses Django's built-in `User` model and the standard `authenticate`/`login`/`logout` flows. Views pass `login_url='login'` to `@login_required` where appropriate.

What to change cautiously
- Checkout flow: `views.checkout` directly sums prices from `CartItem` / `MenuItem` and creates `Order`/`OrderItem`. Any pricing/discount logic should be consolidated here.
- Cart merging: `_merge_session_cart_to_db` must handle duplicate items and integer conversions — mistakes cause duplicated rows or wrong quantities.

If you are making edits
- Update templates in `main/templates/main/` and static assets in `main/static/` together for UI changes.
- When adding new models, run `makemigrations` then `migrate`. Keep migrations in `main/migrations/`.

Where to look for more context
- `main/views.py` — primary business logic and best single-file summary of runtime behavior.
- `main/models.py` — definitive data model and relationships.
- `zwiggy/zwiggy/settings.py` — environment, DB and static/media configuration.

Questions to ask the maintainer before non-trivial changes
- Should we support external DBs (Postgres) or CI-run tests? (no CI config in repo)
- Is there a frontend build step (React) expected upstream? README mentions React but repo lacks a frontend source — confirm intended structure.

Feedback
- If anything above is inaccurate or missing (for example a hidden frontend folder or CI), tell me and I will update this guide.
