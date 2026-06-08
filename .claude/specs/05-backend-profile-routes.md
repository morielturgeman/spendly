# Spec: Backend Routes for Profile Page

## Overview
This step wires the `/profile` route to real database data, replacing the hardcoded dummy context
from Step 4 with live queries. The logged-in user's name, email, and `member_since` date are fetched
from the `users` table. Their expense stats (total spent, transaction count, top category) and recent
transactions are computed from the `expenses` table. This is the first step where the frontend and
backend are connected end-to-end for the profile view.

## Depends on
- Step 1: Database setup (`users` and `expenses` tables must exist)
- Step 2: Registration (users must be creatable with real data)
- Step 3: Login + Logout (session must contain `user_id`)
- Step 4: Profile page UI (the template must already exist with all expected template variables)

## Routes
- `GET /profile` — already exists; modify to query the DB instead of returning hardcoded data — logged-in only

No new routes.

## Database changes
No database changes. The existing `users` and `expenses` tables are sufficient.

## Templates
- **Modify:** `templates/profile.html` — update to handle the case where `transactions` or `categories`
  lists are empty (show a friendly "No expenses yet" message instead of an empty table/list).

## Files to change
- `database/db.py` — add the following helper functions:
  - `get_user_by_id(user_id)` — fetch a single user row by primary key
  - `get_expense_stats(user_id)` — return a dict with `total_spent` (float), `transaction_count` (int), `top_category` (str or None)
  - `get_recent_expenses(user_id, limit=5)` — return the most recent `limit` expense rows for the user, ordered by `date DESC`
  - `get_category_totals(user_id)` — return a list of dicts `{name, total, pct}` ordered by total DESC

- `app.py` — update the `/profile` route to:
  - Call `get_user_by_id(session["user_id"])` and `abort(404)` if not found
  - Call the new DB helpers to build `user`, `stats`, `transactions`, and `categories` context
  - Format `user["created_at"]` into a human-readable `member_since` string (e.g. "January 2024")
  - Format monetary values as `$X,XXX.XX` strings before passing to the template
  - Assign each category a `cls` value (`cat-1` through `cat-5`) based on rank order
  - Remove all hardcoded dummy dicts/lists

## Files to create
No new files.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — use raw sqlite3 via `get_db()`
- Parameterised queries only — never f-strings or string concatenation in SQL
- Passwords hashed with werkzeug (no auth changes in this step)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- `get_db()` connections must be closed in a `finally` block or after every query
- `top_category` should be `None` (render as "—" in template) when there are no expenses
- Percentage values for categories must be integer-rounded and sum to ≤ 100
- `member_since` must be derived from `users.created_at`, not hardcoded

## Definition of done
- [ ] Visiting `/profile` while logged in shows the real name and email of the logged-in user
- [ ] `member_since` reflects the actual `created_at` date from the `users` table
- [ ] Total spent is the correct sum of all the user's expenses
- [ ] Transaction count matches the actual number of expense rows for that user
- [ ] Top category is the category with the highest total spend
- [ ] Recent transactions table shows the 5 most recent expenses ordered by date descending
- [ ] Category breakdown shows per-category totals with correct percentages
- [ ] A freshly registered user with no expenses sees "No expenses yet" (or equivalent) in the transactions section
- [ ] No hardcoded dummy data remains in the `/profile` route in `app.py`
- [ ] All DB helpers live in `database/db.py`, not inline in `app.py`
