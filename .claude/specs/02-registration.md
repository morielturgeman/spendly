# Spec: Registration

## Overview
Implement user registration so that new visitors can create a Spendly account
with their name, email address, and a hashed password. The `/register` route
already renders the form (GET); this step wires up the POST handler, writes the
user to the database, and starts a session so the user is immediately logged in
after sign-up.

## Depends on
- Step 1 — Database Setup: `database/db.py` must expose `get_db()` and
  `init_db()` with a `users` table before this step can be implemented.

## Routes
- `GET  /register` — render registration form — public (already exists, no change needed)
- `POST /register` — validate input, hash password, insert user, start session, redirect to `/dashboard` — public

## Database changes
New `users` table (created in Step 1 — included here for reference):

```sql
CREATE TABLE IF NOT EXISTS users (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT    NOT NULL,
    email      TEXT    NOT NULL UNIQUE,
    password   TEXT    NOT NULL,
    created_at TEXT    NOT NULL DEFAULT (datetime('now'))
);
```

`database/db.py` must provide:
- `create_user(name, email, password_hash)` — inserts a row and returns the new `id`
- `get_user_by_email(email)` — returns a row dict or `None`

## Templates
- **Modify:** `templates/register.html`
  - Display server-side `{{ error }}` block (already present in template — confirm it renders correctly)
  - No structural changes required

## Files to change
- `app.py` — add POST handler for `/register`; import `session`, `redirect`, `url_for`, `request` from Flask; import `generate_password_hash` from `werkzeug.security`; import db helpers
- `database/db.py` — add `create_user()` and `get_user_by_email()` functions (if not already present)

## Files to create
None — all necessary files already exist.

## New dependencies
No new dependencies (`werkzeug` is already in `requirements.txt`).

## Rules for implementation
- No SQLAlchemy or ORMs — use raw SQLite via `get_db()`
- Parameterised queries only — never interpolate user input into SQL strings
- Hash passwords with `werkzeug.security.generate_password_hash`
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Set `app.secret_key` (read from env var `SECRET_KEY`, fall back to a dev default)
- Store `user_id` and `user_name` in `session` after successful registration
- On duplicate email, re-render the form with `error="An account with that email already exists."`
- On missing/short fields, re-render the form with an appropriate `error` message
- Password minimum length: 8 characters (validate server-side)
- After successful registration redirect to `/dashboard` (placeholder route is acceptable for now)

## Definition of done
- [ ] Submitting the form with valid data creates a row in the `users` table
- [ ] The stored password is a Werkzeug hash, not plain text
- [ ] After registration the user is redirected (HTTP 302) to `/dashboard`
- [ ] `session['user_id']` is set to the new user's id after registration
- [ ] Submitting with an already-registered email re-renders `/register` with an error message visible on the page
- [ ] Submitting with a password shorter than 8 characters re-renders `/register` with a validation error
- [ ] Submitting with an empty name or email re-renders `/register` with a validation error
- [ ] The registration form is still accessible at `GET /register` without logging in
