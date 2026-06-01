# Spec: Login and Logout

## Overview
This step implements the login and logout flows for Spendly. Users can submit their email and password to authenticate; on success, their `user_id` and `user_name` are stored in the Flask session. The logout route clears the session and redirects to the landing page. This is the first step that enables access-controlled routes in later steps.

## Depends on
- Step 01: Database setup (`users` table, `get_db()`)
- Step 02: Registration (`create_user`, `get_user_by_email`, password hashing in place)

## Routes
- `GET /login` — render login form — public
- `POST /login` — validate credentials, set session, redirect to `/dashboard` — public
- `GET /logout` — clear session, redirect to `/` — logged-in (or gracefully handle if not logged in)

## Database changes
No database changes. The `users` table from Step 01 already has `email` and `password_hash` columns.

## Templates
- **Modify:** `templates/login.html` — add a POST form with email and password fields, and an error display area (currently renders but has no form)

## Files to change
- `app.py` — implement `login()` with GET/POST, implement `logout()`; also resolve the existing merge conflict markers at the top of the file
- `templates/login.html` — add form, error display, link to register page

## Files to create
No new files.

## New dependencies
No new dependencies. `werkzeug.security.check_password_hash` is already available via the existing `werkzeug` install.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only (`?` placeholders)
- Passwords verified with `werkzeug.security.check_password_hash` — never compared in plain text
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- `logout` must call `session.clear()` before redirecting
- `login` POST must re-render the form with an error on bad credentials — never redirect to an error page
- Resolve the merge conflict in `app.py` before adding new code; the correct final imports are: `os`, `Flask`, `render_template`, `request`, `redirect`, `url_for`, `session`, `generate_password_hash`, `check_password_hash`, `init_db`, `create_user`, `get_user_by_email`
- `get_user_by_email` already exists in `database/db.py` — do not reimplement it

## Definition of done
- [ ] `GET /login` renders the login form without errors
- [ ] Submitting the form with a valid email/password sets `session["user_id"]` and redirects to `/dashboard`
- [ ] Submitting with an unknown email shows an inline error on the login page
- [ ] Submitting with a wrong password shows an inline error on the login page
- [ ] `GET /logout` clears the session and redirects to `/`
- [ ] After logout, navigating to `/logout` again does not crash — it simply redirects cleanly
- [ ] The merge conflict markers in `app.py` are fully resolved
- [ ] All tests pass: `pytest`
