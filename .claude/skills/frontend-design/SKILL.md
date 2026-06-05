---
name: spendly-ui-designer
description: >
  Generates modern, production-ready UI pages and components for Spendly, a personal
  expense tracker built with Flask, Jinja2, and vanilla CSS/JS. Use this skill any time
  the user says things like "design the ___ page", "create UI for ___", "build a component
  for ___", "redesign ___", or "improve the look of ___" in the context of Spendly. Also
  trigger when the user shares a screenshot of Spendly and asks for improvements, or says
  the current design looks bad. Produces clean fintech-style HTML templates + CSS that
  match the existing project conventions.
---

# Spendly UI Designer

Generates polished, consistent UI for the Spendly expense tracker.
Spendly is a **Flask + Jinja2 + SQLite** app with **vanilla JS only** — no React, no npm.

## Tech Constraints (non-negotiable)
- Templates are Jinja2 HTML files; all must `{% extends "base.html" %}`
- Vanilla CSS only — no Tailwind, no Bootstrap, no preprocessors
- Vanilla JS only — no React, no jQuery, no npm packages
- Icons: Lucide Icons via CDN (`<script src="https://unpkg.com/lucide@latest"></script>`) or inline SVGs
- No new pip packages; no inline `<style>` tags — CSS goes in a new `.css` file
- All internal links use `{{ url_for('route_name') }}` — never hardcode URLs
- New routes → `app.py`; DB logic → `database/db.py`; new pages → `templates/`; CSS → `static/css/`

## Design System

### Color Palette
```css
/* Core tokens — use these in all new CSS files */
--color-bg:           #F8F9FC;   /* page background */
--color-surface:      #FFFFFF;   /* card / panel background */
--color-border:       #E8ECF4;   /* subtle dividers */
--color-text-primary: #1A1D2E;   /* headings */
--color-text-secondary:#6B7280;  /* labels, helper text */
--color-accent:       #6366F1;   /* primary CTA (indigo) */
--color-accent-light: #EEF2FF;   /* accent backgrounds / badges */
--color-success:      #10B981;   /* income / positive */
--color-success-light:#D1FAE5;
--color-danger:       #EF4444;   /* expenses / negative */
--color-danger-light: #FEE2E2;
--color-warning:      #F59E0B;   /* caution / pending */
--color-warning-light:#FEF3C7;
```

### Typography
```css
--font-sans: 'DM Sans', 'Inter', system-ui, sans-serif;
/* Load via: <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet"> */
--text-xs:   0.75rem;   /* 12px — labels, badges */
--text-sm:   0.875rem;  /* 14px — body, table cells */
--text-base: 1rem;      /* 16px — default */
--text-lg:   1.125rem;  /* 18px — card titles */
--text-xl:   1.25rem;   /* 20px — section headers */
--text-2xl:  1.5rem;    /* 24px — page titles */
--text-3xl:  1.875rem;  /* 30px — hero numbers */
```

### Spacing Grid (8px base)
```
4px  → micro gaps (icon+label, badge padding)
8px  → tight spacing (list items, form field padding)
12px → inner card padding (compact)
16px → standard padding, grid gaps
24px → card padding, section gaps
32px → page sections
48px → large section breaks
```

### Component Primitives
```css
/* Card */
.card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0,0,0,.06), 0 1px 2px rgba(0,0,0,.04);
}

/* Badge */
.badge {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 2px 10px; border-radius: 999px;
  font-size: var(--text-xs); font-weight: 600; letter-spacing: .02em;
}
.badge-expense { background: var(--color-danger-light); color: var(--color-danger); }
.badge-income  { background: var(--color-success-light); color: var(--color-success); }
.badge-neutral { background: var(--color-accent-light); color: var(--color-accent); }

/* Button */
.btn { display: inline-flex; align-items: center; gap: 6px; padding: 8px 16px;
  border-radius: 8px; font-size: var(--text-sm); font-weight: 500; cursor: pointer;
  border: none; transition: all .15s ease; }
.btn-primary { background: var(--color-accent); color: #fff; }
.btn-primary:hover { background: #4F46E5; box-shadow: 0 4px 12px rgba(99,102,241,.3); }
.btn-ghost { background: transparent; color: var(--color-text-secondary); border: 1px solid var(--color-border); }
.btn-ghost:hover { background: var(--color-bg); }

/* Input */
.input {
  width: 100%; padding: 10px 12px; border: 1.5px solid var(--color-border);
  border-radius: 8px; font-size: var(--text-sm); background: var(--color-surface);
  color: var(--color-text-primary); transition: border-color .15s;
}
.input:focus { outline: none; border-color: var(--color-accent);
  box-shadow: 0 0 0 3px rgba(99,102,241,.1); }
```

### Navigation (base.html sidebar pattern)
The sidebar is the primary nav. Active links use `--color-accent-light` background
and `--color-accent` icon/text color. Nav items: Dashboard, Expenses, Add Expense,
Categories, Profile. Always show Spendly wordmark + a small wallet icon at the top.

### Iconography
Use Lucide icons initialized with `lucide.createIcons()` at end of body.
Common icons for Spendly:
- `wallet` — app logo / balance
- `trending-down` — expenses
- `trending-up` — income  
- `plus-circle` — add expense
- `receipt` — expense list
- `pie-chart` — categories
- `user` — profile
- `log-out` — logout
- `calendar` — date filters
- `filter` — filter/search
- `edit-2` — edit action
- `trash-2` — delete action
- `check-circle` — success state

---

## Output Format

For every UI request, produce:

### 1. Layout Brief (3–5 lines)
Describe the layout structure, key sections, and 1–2 important UX decisions. Be concise.

### 2. Template file: `templates/<page>.html`
Full Jinja2 template extending base.html.
```html
{% extends "base.html" %}
{% block title %}Page Title — Spendly{% endblock %}
{% block head %}
<!-- page-specific font/icon imports if needed -->
<link rel="stylesheet" href="{{ url_for('static', filename='css/<page>.css') }}">
{% endblock %}
{% block content %}
<!-- page markup -->
{% endblock %}
```

### 3. CSS file: `static/css/<page>.css`
Clean, well-organized CSS using the design tokens above.
Structure:
```css
/* ============================================================
   <PAGE NAME>  |  spendly
   ============================================================ */

/* 1. Layout -------------------------------------------------- */
/* 2. Header / Hero ------------------------------------------ */
/* 3. Components --------------------------------------------- */
/* 4. States (empty, loading, error) ------------------------- */
/* 5. Responsive --------------------------------------------- */
```

### 4. (If needed) JS snippet for `static/js/main.js`
Vanilla JS only. Keep it short and purposeful — DOM manipulation, form validation,
chart rendering with a CDN-loaded library (Chart.js is OK via CDN).

---

## Design Rules

**Do:**
- Use the token palette above — never introduce new brand colors without flagging
- Rounded corners (8–12px on cards, 8px on inputs/buttons, 999px on pills/badges)
- Soft shadows on cards, stronger on modals/dropdowns
- Consistent 8px grid spacing
- Amount values: right-align numbers in tables, use `font-variant-numeric: tabular-nums`
- Negative amounts in `--color-danger`, positive in `--color-success`
- Empty states: show an icon + friendly message + a CTA button
- Skeleton loaders for async data (if JS is involved)

**Don't:**
- Inline `<style>` blocks in templates
- Use arbitrary hex colors outside the token set
- Add new fonts without mentioning it
- Use JS frameworks or `npm install` anything
- Hardcode URLs — always `url_for()`
- Clutter cards with too many actions — max 2–3 visible, rest in a `•••` menu
- Use dense tables without zebra-striping or hover states

---

## Consistency Check

Before generating code, ask yourself:
1. Does this page have a counterpart in the existing repo? If yes, mirror its layout/nav.
2. Are the color tokens from the palette above? If unclear → ask for a screenshot.
3. Would a new developer recognize this as "the same app" as landing.html / base.html?

If the user hasn't shared screenshots and the request touches a page that extends base.html,
ask: *"Could you share a screenshot of the current design so I can match the style exactly?"*
— but only if it's genuinely needed for consistency; don't block simple add-form requests.

---

## Common Page Patterns

### Dashboard (`/`)
- Summary stat cards row: Total Spent, This Month, Top Category, Budget Left
- Recent Expenses table (5–10 rows) with category badge + amount
- Spending by Category donut chart (Chart.js via CDN, or CSS-only bars)
- Quick Add Expense floating button (bottom-right on mobile)

### Expense List (`/expenses`)
- Filter bar: date range picker, category dropdown, search input
- Sortable table: Date | Description | Category | Amount | Actions
- Pagination footer
- Empty state when no results

### Add/Edit Expense (`/expenses/add`, `/expenses/<id>/edit`)
- Single-column form, max-width 520px, centered
- Fields: Amount (large input), Description, Category (select), Date (date picker), Notes (textarea)
- Submit + Cancel buttons
- Success flash message on redirect

### Category Manager
- Grid of category cards (icon, name, color swatch, expense count)
- Add category inline form or modal-style slide-in panel

### Profile (`/profile`)
- Avatar placeholder + name/email
- Edit form: name, email, currency preference
- Danger zone: delete account (always at bottom, red-tinted card)

### Login / Register
- Centered card, max 400px
- App logo at top
- Fields with floating labels or clean stacked labels
- Social proof tagline under the logo ("Track every rupee, effortlessly.")

---

## References

- `references/design-tokens.css` — copy-paste ready CSS variables
- `references/component-examples.html` — standalone HTML kitchen sink for testing

Read these when generating complex pages to ensure token accuracy.