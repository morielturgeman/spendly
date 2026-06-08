# Spec: Date Filter for Profile Page

## Overview
This step adds a date-range filter to the profile page so users can narrow all
displayed data — transaction history, summary stats, and category breakdown —
to a chosen time window. The filter is driven by query-string parameters
(`from_date` and `to_date`) so the filtered view is bookmarkable and shareable.
A row of preset quick-select buttons (This Month, Last 30 Days, Last 3 Months,
All Time) lets users jump to common ranges without typing dates. This is a
pure "connect the dots" step: the database schema is unchanged; only the helper
signatures, the route, and the template need updating.

## Depends on
- Step 05: Backend profile routes — `get_recent_expenses`, `get_expense_stats`,
  and `get_category_totals` must already exist in `database/db.py`, and the
  `/profile` route must already pass live data to `profile.html`.

## Routes
- `GET /profile` — already exists; extend to accept optional query params
  `from_date` (YYYY-MM-DD) and `to_date` (YYYY-MM-DD); apply them as WHERE
  filters in every DB call — logged-in only

No new routes.

## Database changes
No database changes. The existing `expenses.date` TEXT column (YYYY-MM-DD) is
directly comparable with string inequality operators in SQLite.

## Templates
- **Modify:** `templates/profile.html`
  - Add a filter bar above the transactions section containing:
    - Preset buttons: "This Month", "Last 30 Days", "Last 3 Months", "All Time"
    - Two `<input type="date">` fields (From / To) with a Submit button for
      custom ranges
  - Highlight the active preset (CSS class `active`) when the current
    `from_date`/`to_date` matches a preset's computed range
  - Display the active date range as a human-readable label beneath the filter
    bar (e.g. "Jun 1 – Jun 8, 2026")
  - All existing sections (stats, transactions, categories) already receive
    filtered data from the route — no structural changes to those sections

## Files to change
- `database/db.py` — update the three helpers to accept optional date bounds:
  - `get_recent_expenses(user_id, limit=5, from_date=None, to_date=None)`
  - `get_expense_stats(user_id, from_date=None, to_date=None)`
  - `get_category_totals(user_id, from_date=None, to_date=None)`
  - When `from_date` or `to_date` is provided, append `AND date >= ?` /
    `AND date <= ?` to the WHERE clause using parameterized placeholders

- `app.py` — update the `/profile` route to:
  - Read `from_date` and `to_date` from `request.args`
  - Validate both values are valid YYYY-MM-DD strings (or None); ignore
    malformed values silently (treat as None)
  - Pass `from_date` and `to_date` to each DB helper
  - Pass `from_date`, `to_date`, and an `active_preset` string to the template
    so the filter bar can render correctly

- `static/css/profile.css` (or the relevant page-specific CSS file) — add
  styles for:
  - `.filter-bar` container
  - `.preset-btn` and `.preset-btn.active`
  - `.date-range-label`
  - Date inputs and submit button

## Files to create
None.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only — never f-strings or string concatenation in SQL
- Passwords hashed with werkzeug (no auth changes in this step)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Date validation in the route must use `datetime.strptime` wrapped in a
  try/except; on failure silently set the value to `None`
- Preset date computation must happen in `app.py` using the `datetime` and
  `date` standard-library modules — not in JavaScript
- The "All Time" preset passes `from_date=None, to_date=None` (no filter)
- Do not use JS frameworks; the preset buttons are plain `<a>` links that
  append query params to the current URL
- Page-specific styles belong in a dedicated CSS file, not inline `<style>` tags

## Definition of done
- [ ] Visiting `/profile` with no query params shows all expenses (All Time)
- [ ] Visiting `/profile?from_date=2026-06-01&to_date=2026-06-30` shows only
      June expenses in every section (stats, transactions, categories)
- [ ] Clicking "This Month" preset redirects to the correct `from_date`/`to_date`
      for the current calendar month
- [ ] Clicking "Last 30 Days" preset shows expenses from the last 30 days
- [ ] Clicking "Last 3 Months" preset shows expenses from the last 90 days
- [ ] The active preset button has a visually distinct `active` state
- [ ] The date-range label below the filter bar reflects the current filter
- [ ] Submitting the custom date inputs with valid dates filters correctly
- [ ] Passing an invalid date string in the URL does not crash the app — it
      falls back to no filter (All Time)
- [ ] A user with no expenses in the selected range sees "No expenses yet"
      (or equivalent) in the transactions section
- [ ] Stats (total spent, transaction count, top category) reflect only the
      filtered date range
- [ ] Category breakdown reflects only the filtered date range
