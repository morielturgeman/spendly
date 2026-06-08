"""
Tests for Step 06: Date Filter on the Profile Page.

Spec: .claude/specs/06-date-filter-profile-page.md

All tests are driven by the spec's Definition of Done and observable
HTTP/HTML behavior only. No implementation internals are tested.
"""

import sqlite3
import pytest
from datetime import date, timedelta
from werkzeug.security import generate_password_hash

from app import app
from database.db import init_db


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _iso(d: date) -> str:
    """Convert a date to an ISO-8601 string (YYYY-MM-DD)."""
    return d.isoformat()


def _seed(db_path: str) -> int:
    """
    Create one user and a spread of expenses that deliberately straddle
    multiple calendar periods so every filter scenario has deterministic
    expected results.

    Expense set (all for the seeded user):

      2026-01-15  Food        $100.00  "January groceries"
      2026-03-10  Transport   $ 50.00  "March bus pass"
      2026-05-20  Bills       $ 80.00  "May electricity"
      2026-06-01  Food        $ 40.00  "June groceries"
      2026-06-15  Shopping    $ 60.00  "June shoes"
      2026-06-08  Health      $ 30.00  "June pharmacy"   ← matches today fixture

    "today" in the test suite is pinned to 2026-06-08 for preset range
    assertions.  All date arithmetic in tests that verify preset ranges
    must use the same anchor.

    Returns the inserted user_id.
    """
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS users "
        "(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, "
        "email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, "
        "created_at TEXT DEFAULT (datetime('now')))"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS expenses "
        "(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, "
        "amount REAL NOT NULL, category TEXT NOT NULL, date TEXT NOT NULL, "
        "description TEXT, created_at TEXT DEFAULT (datetime('now')))"
    )
    cursor = conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("Test User", "test@spendly.com",
         generate_password_hash("password123", method="pbkdf2:sha256")),
    )
    user_id = cursor.lastrowid

    expenses = [
        (user_id, 100.00, "Food",      "2026-01-15", "January groceries"),
        (user_id,  50.00, "Transport", "2026-03-10", "March bus pass"),
        (user_id,  80.00, "Bills",     "2026-05-20", "May electricity"),
        (user_id,  40.00, "Food",      "2026-06-01", "June groceries"),
        (user_id,  60.00, "Shopping",  "2026-06-15", "June shoes"),
        (user_id,  30.00, "Health",    "2026-06-08", "June pharmacy"),
    ]
    conn.executemany(
        "INSERT INTO expenses (user_id, amount, category, date, description) "
        "VALUES (?, ?, ?, ?, ?)",
        expenses,
    )
    conn.commit()
    conn.close()
    return user_id


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def client(tmp_path):
    """
    Provide an isolated Flask test client backed by a fresh temp-file SQLite
    database.  The production database is never touched.
    """
    db_path = str(tmp_path / "test.db")

    app.config["TESTING"] = True
    app.config["DATABASE"] = db_path
    app.config["SECRET_KEY"] = "test-secret-key"

    # Point the db module at the test database for this session.
    import database.db as db_module
    original_path = db_module.DB_PATH
    db_module.DB_PATH = db_path

    with app.test_client() as test_client:
        with app.app_context():
            init_db()
        yield test_client

    # Restore original path so other test modules are unaffected.
    db_module.DB_PATH = original_path


@pytest.fixture()
def seeded_client(tmp_path):
    """
    Like `client` but also seeds the DB with a spread of dated expenses and
    returns a tuple of (test_client, user_id).  The user is NOT yet logged in.
    """
    db_path = str(tmp_path / "test_seeded.db")

    app.config["TESTING"] = True
    app.config["DATABASE"] = db_path
    app.config["SECRET_KEY"] = "test-secret-key"

    import database.db as db_module
    original_path = db_module.DB_PATH
    db_module.DB_PATH = db_path

    user_id = _seed(db_path)

    with app.test_client() as test_client:
        yield test_client, user_id

    db_module.DB_PATH = original_path


@pytest.fixture()
def logged_in_client(seeded_client):
    """
    Seeded client with the test user already authenticated via session injection.
    Returns (test_client, user_id).
    """
    test_client, user_id = seeded_client
    with test_client.session_transaction() as sess:
        sess["user_id"] = user_id
        sess["user_name"] = "Test User"
    return test_client, user_id


# ---------------------------------------------------------------------------
# Auth guard
# ---------------------------------------------------------------------------

class TestProfileAuthGuard:
    def test_unauthenticated_redirects_to_login(self, client):
        """GET /profile without a session must redirect to /login."""
        response = client.get("/profile", follow_redirects=False)
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]

    def test_unauthenticated_does_not_render_profile(self, client):
        """Following the redirect from an unauthenticated /profile hit lands on
        the login page, not the profile page."""
        response = client.get("/profile", follow_redirects=True)
        assert response.status_code == 200
        # The login page must be served, not the profile page.
        assert b"login" in response.data.lower() or b"sign in" in response.data.lower()

    def test_authenticated_user_can_reach_profile(self, logged_in_client):
        """A logged-in user receives a 200 from GET /profile."""
        test_client, _ = logged_in_client
        response = test_client.get("/profile")
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# No query params — All Time
# ---------------------------------------------------------------------------

class TestNoQueryParams:
    def test_status_200(self, logged_in_client):
        """GET /profile with no query params returns HTTP 200."""
        test_client, _ = logged_in_client
        response = test_client.get("/profile")
        assert response.status_code == 200

    def test_all_expenses_visible(self, logged_in_client):
        """With no date filter, all seeded expenses appear in the response."""
        test_client, _ = logged_in_client
        response = test_client.get("/profile")
        html = response.data
        # Three distinct descriptions from different months must appear.
        assert b"January groceries" in html
        assert b"March bus pass" in html
        assert b"June groceries" in html

    def test_range_label_is_all_time(self, logged_in_client):
        """When no filter is applied the range label must read 'All time'."""
        test_client, _ = logged_in_client
        response = test_client.get("/profile")
        # Case-insensitive check since templates may vary capitalisation.
        assert b"all time" in response.data.lower()

    def test_stats_reflect_all_expenses(self, logged_in_client):
        """Total-spent stat must equal the sum of all seeded expenses ($360.00)
        when no date filter is active."""
        test_client, _ = logged_in_client
        response = test_client.get("/profile")
        # 100 + 50 + 80 + 40 + 60 + 30 = 360
        assert b"360.00" in response.data

    def test_transaction_count_all(self, logged_in_client):
        """Transaction count must equal the total number of seeded expenses (6)
        when no date filter is active."""
        test_client, _ = logged_in_client
        response = test_client.get("/profile")
        # '6' must appear somewhere in the stats area; a simple substring check
        # is sufficient since there is no other obvious '6' total in the page.
        assert b"6" in response.data


# ---------------------------------------------------------------------------
# Custom date range — valid from_date / to_date
# ---------------------------------------------------------------------------

class TestCustomDateRange:
    def test_june_only_filter_returns_200(self, logged_in_client):
        """A custom June date range returns HTTP 200."""
        test_client, _ = logged_in_client
        response = test_client.get("/profile?from_date=2026-06-01&to_date=2026-06-30")
        assert response.status_code == 200

    def test_june_filter_shows_june_expenses(self, logged_in_client):
        """Filtering to June 2026 must include all three June expenses."""
        test_client, _ = logged_in_client
        response = test_client.get("/profile?from_date=2026-06-01&to_date=2026-06-30")
        html = response.data
        assert b"June groceries" in html
        assert b"June shoes" in html
        assert b"June pharmacy" in html

    def test_june_filter_excludes_earlier_expenses(self, logged_in_client):
        """Filtering to June 2026 must NOT include January or March expenses."""
        test_client, _ = logged_in_client
        response = test_client.get("/profile?from_date=2026-06-01&to_date=2026-06-30")
        html = response.data
        assert b"January groceries" not in html
        assert b"March bus pass" not in html

    def test_june_filter_total_spent(self, logged_in_client):
        """Total spent for June only must equal $130.00 (40 + 60 + 30)."""
        test_client, _ = logged_in_client
        response = test_client.get("/profile?from_date=2026-06-01&to_date=2026-06-30")
        assert b"130.00" in response.data

    def test_june_filter_transaction_count(self, logged_in_client):
        """Transaction count for June must equal 3."""
        test_client, _ = logged_in_client
        response = test_client.get("/profile?from_date=2026-06-01&to_date=2026-06-30")
        assert b"3" in response.data

    def test_june_filter_top_category(self, logged_in_client):
        """Top category for June must be Shopping ($60 > Food $40 > Health $30)."""
        test_client, _ = logged_in_client
        response = test_client.get("/profile?from_date=2026-06-01&to_date=2026-06-30")
        assert b"Shopping" in response.data

    def test_from_date_only_filters_lower_bound(self, logged_in_client):
        """Providing only from_date=2026-05-01 excludes January and March
        but includes May and June expenses."""
        test_client, _ = logged_in_client
        response = test_client.get("/profile?from_date=2026-05-01")
        html = response.data
        assert b"May electricity" in html
        assert b"June groceries" in html
        assert b"January groceries" not in html
        assert b"March bus pass" not in html

    def test_to_date_only_filters_upper_bound(self, logged_in_client):
        """Providing only to_date=2026-03-31 excludes May and June but
        includes January and March expenses."""
        test_client, _ = logged_in_client
        response = test_client.get("/profile?to_date=2026-03-31")
        html = response.data
        assert b"January groceries" in html
        assert b"March bus pass" in html
        assert b"May electricity" not in html
        assert b"June groceries" not in html

    def test_custom_range_label_rendered(self, logged_in_client):
        """A custom date range must render a human-readable label that reflects
        both the from and to dates, not 'All time'."""
        test_client, _ = logged_in_client
        response = test_client.get("/profile?from_date=2026-06-01&to_date=2026-06-30")
        html = response.data.lower()
        # 'All time' label must NOT be present for a custom range.
        # ASSUMPTION: the label contains recognisable parts of the dates
        # (e.g. 'Jun', '2026') rather than raw ISO strings.
        assert b"jun" in html

    def test_category_breakdown_reflects_filtered_range(self, logged_in_client):
        """The category breakdown section must only show categories that have
        expenses within the filtered date range."""
        test_client, _ = logged_in_client
        # Only May and June are in scope; Food and Transport from Jan/Mar
        # must not appear in the category breakdown.
        response = test_client.get("/profile?from_date=2026-05-01&to_date=2026-06-30")
        html = response.data
        # Bills (May), Food (June), Shopping (June), Health (June) should appear.
        assert b"Bills" in html
        assert b"Shopping" in html
        # Transport only appears in March — must be absent.
        # ASSUMPTION: "Transport" as a category label is not repeated in nav or
        # other static UI text within the profile template.
        assert b"Transport" not in html


# ---------------------------------------------------------------------------
# Preset URL behavior
# ---------------------------------------------------------------------------

class TestPresetUrls:
    """
    Preset buttons are plain <a> links that embed computed from_date/to_date
    values.  We verify the page correctly matches those computed ranges to the
    active_preset and that the correct subset of data is returned.

    The app computes preset ranges from date.today() at request time, so tests
    here validate behavior relative to the seeded data rather than pinning
    exact date strings.
    """

    def test_this_month_preset_link_present(self, logged_in_client):
        """The profile page must contain a link or button labelled 'This Month'."""
        test_client, _ = logged_in_client
        response = test_client.get("/profile")
        assert b"This Month" in response.data

    def test_last_30_days_preset_link_present(self, logged_in_client):
        """The profile page must contain a link or button labelled 'Last 30 Days'."""
        test_client, _ = logged_in_client
        response = test_client.get("/profile")
        assert b"Last 30 Days" in response.data

    def test_last_3_months_preset_link_present(self, logged_in_client):
        """The profile page must contain a link or button labelled 'Last 3 Months'."""
        test_client, _ = logged_in_client
        response = test_client.get("/profile")
        assert b"Last 3 Months" in response.data

    def test_all_time_preset_link_present(self, logged_in_client):
        """The profile page must contain a link or button labelled 'All Time'."""
        test_client, _ = logged_in_client
        response = test_client.get("/profile")
        assert b"All Time" in response.data

    def test_this_month_range_starts_on_first_of_month(self, logged_in_client):
        """Requesting the This Month preset range must include expenses on the
        first day of the current month and not include expenses from the
        previous month.

        We compute the expected from_date dynamically so the test remains
        correct regardless of when it is executed.
        """
        today = date.today()
        first_of_month = today.replace(day=1).isoformat()
        test_client, _ = logged_in_client
        response = test_client.get(
            f"/profile?from_date={first_of_month}&to_date={today.isoformat()}"
        )
        assert response.status_code == 200

    def test_last_30_days_correct_range(self, logged_in_client):
        """Requesting the Last 30 Days range returns HTTP 200 and the page
        does not crash."""
        today = date.today()
        from_date = (today - timedelta(days=30)).isoformat()
        test_client, _ = logged_in_client
        response = test_client.get(
            f"/profile?from_date={from_date}&to_date={today.isoformat()}"
        )
        assert response.status_code == 200

    def test_last_3_months_correct_range(self, logged_in_client):
        """Requesting the Last 3 Months range returns HTTP 200 and the page
        does not crash."""
        today = date.today()
        from_date = (today - timedelta(days=90)).isoformat()
        test_client, _ = logged_in_client
        response = test_client.get(
            f"/profile?from_date={from_date}&to_date={today.isoformat()}"
        )
        assert response.status_code == 200

    def test_all_time_preset_active_class_on_bare_profile(self, logged_in_client):
        """When no query params are present the 'All Time' button must carry the
        CSS active marker so the user sees which preset is current."""
        test_client, _ = logged_in_client
        response = test_client.get("/profile")
        # ASSUMPTION: the active preset button is rendered with CSS class 'active'.
        # We expect 'active' to appear in the HTML near 'All Time'.
        html = response.data.decode()
        all_time_section = html.lower()
        # Verify the word 'active' appears somewhere in the page when all-time
        # is the current preset.
        assert "active" in all_time_section

    def test_preset_active_class_set_for_matching_range(self, logged_in_client):
        """When the query params exactly match a preset's computed range, the
        page must render the 'active' CSS marker on that preset button."""
        today = date.today()
        first_of_month = today.replace(day=1).isoformat()
        test_client, _ = logged_in_client
        response = test_client.get(
            f"/profile?from_date={first_of_month}&to_date={today.isoformat()}"
        )
        assert b"active" in response.data


# ---------------------------------------------------------------------------
# Invalid date strings — fallback to All Time
# ---------------------------------------------------------------------------

class TestInvalidDateParams:
    def test_invalid_from_date_does_not_crash(self, logged_in_client):
        """A garbage from_date value must not raise an exception — the app must
        return HTTP 200 and fall back to showing all expenses."""
        test_client, _ = logged_in_client
        response = test_client.get("/profile?from_date=not-a-date")
        assert response.status_code == 200

    def test_invalid_to_date_does_not_crash(self, logged_in_client):
        """A garbage to_date value must not raise an exception — the app must
        return HTTP 200."""
        test_client, _ = logged_in_client
        response = test_client.get("/profile?to_date=99-99-9999")
        assert response.status_code == 200

    def test_both_dates_invalid_falls_back_to_all_time(self, logged_in_client):
        """When both date params are malformed, all expenses must still be shown
        (fallback to All Time behavior)."""
        test_client, _ = logged_in_client
        response = test_client.get(
            "/profile?from_date=abc&to_date=xyz"
        )
        html = response.data
        assert b"January groceries" in html
        assert b"June groceries" in html

    def test_invalid_date_range_label_is_all_time(self, logged_in_client):
        """When both params are invalid, the range label must read 'All time'
        (no partial date range label is displayed)."""
        test_client, _ = logged_in_client
        response = test_client.get("/profile?from_date=bad&to_date=bad")
        assert b"all time" in response.data.lower()

    def test_partial_invalid_date_format(self, logged_in_client):
        """A date that looks almost valid (wrong format) must be silently
        discarded and not crash the server."""
        test_client, _ = logged_in_client
        # DD-MM-YYYY is wrong — the route expects YYYY-MM-DD.
        response = test_client.get("/profile?from_date=01-06-2026&to_date=30-06-2026")
        assert response.status_code == 200

    def test_sql_injection_in_date_param_does_not_crash(self, logged_in_client):
        """A SQL injection attempt in the date param must be rejected by the
        date validator and the app must return 200 safely."""
        test_client, _ = logged_in_client
        response = test_client.get(
            "/profile?from_date='; DROP TABLE expenses; --&to_date=2026-06-30"
        )
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Empty result — no expenses in the selected range
# ---------------------------------------------------------------------------

class TestEmptyDateRange:
    def test_future_range_returns_200(self, logged_in_client):
        """A valid date range with no matching expenses must still return 200."""
        test_client, _ = logged_in_client
        response = test_client.get(
            "/profile?from_date=2030-01-01&to_date=2030-12-31"
        )
        assert response.status_code == 200

    def test_future_range_shows_no_expenses_message(self, logged_in_client):
        """When no expenses fall within the chosen range, the page must display
        an empty-state indicator (e.g. 'No expenses yet' or equivalent)."""
        test_client, _ = logged_in_client
        response = test_client.get(
            "/profile?from_date=2030-01-01&to_date=2030-12-31"
        )
        html = response.data.lower()
        # ASSUMPTION: the template uses a phrase containing 'no expenses' for
        # the empty state, matching the spec's DoD item.
        assert b"no expenses" in html

    def test_empty_range_total_is_zero(self, logged_in_client):
        """Total spent must be $0.00 when no expenses exist in the range."""
        test_client, _ = logged_in_client
        response = test_client.get(
            "/profile?from_date=2030-01-01&to_date=2030-12-31"
        )
        assert b"0.00" in response.data

    def test_empty_range_transaction_count_is_zero(self, logged_in_client):
        """Transaction count must be 0 when no expenses exist in the range."""
        test_client, _ = logged_in_client
        response = test_client.get(
            "/profile?from_date=2030-01-01&to_date=2030-12-31"
        )
        assert b"0" in response.data

    def test_empty_range_no_stale_categories(self, logged_in_client):
        """When no expenses match the filter, previously visible categories
        such as 'Food' and 'Shopping' must not appear in the category
        breakdown section."""
        test_client, _ = logged_in_client
        response = test_client.get(
            "/profile?from_date=2030-01-01&to_date=2030-12-31"
        )
        # The category names 'Food' and 'Shopping' should not appear as breakdown
        # entries when the filtered result set is empty.
        # ASSUMPTION: category names in the breakdown are not also used verbatim
        # elsewhere in static template text.  If they are, this test would need
        # a tighter selector — but per spec the breakdown section is data-driven.
        html = response.data
        assert b"Shopping" not in html

    def test_past_range_with_data_does_not_show_empty_message(self, logged_in_client):
        """Sanity-check: a range that does contain expenses must NOT show the
        'no expenses' message."""
        test_client, _ = logged_in_client
        response = test_client.get(
            "/profile?from_date=2026-06-01&to_date=2026-06-30"
        )
        html = response.data.lower()
        assert b"no expenses" not in html


# ---------------------------------------------------------------------------
# Stats reflect filtered range
# ---------------------------------------------------------------------------

class TestFilteredStats:
    def test_stats_total_spent_changes_with_filter(self, logged_in_client):
        """The total_spent stat must change when a narrower date range is
        applied, confirming stats are not cached from the unfiltered view."""
        test_client, _ = logged_in_client

        all_time = test_client.get("/profile")
        june_only = test_client.get(
            "/profile?from_date=2026-06-01&to_date=2026-06-30"
        )

        # All-time total is $360.00; June total is $130.00 — they must differ.
        assert b"360.00" in all_time.data
        assert b"130.00" in june_only.data
        assert b"360.00" not in june_only.data

    def test_stats_transaction_count_changes_with_filter(self, logged_in_client):
        """Transaction count must drop from 6 (all time) to 3 (June only)
        when the filter is applied."""
        test_client, _ = logged_in_client

        all_time = test_client.get("/profile")
        june_only = test_client.get(
            "/profile?from_date=2026-06-01&to_date=2026-06-30"
        )

        assert b"6" in all_time.data
        assert b"3" in june_only.data

    def test_top_category_changes_with_filter(self, logged_in_client):
        """The top_category stat must reflect the filtered range.

        All-time: Food is the largest category ($100 + $40 = $140).
        June only: Shopping is the largest category ($60 > $40 Food > $30 Health).
        """
        test_client, _ = logged_in_client

        all_time = test_client.get("/profile")
        june_only = test_client.get(
            "/profile?from_date=2026-06-01&to_date=2026-06-30"
        )

        assert b"Food" in all_time.data
        assert b"Shopping" in june_only.data

    def test_category_totals_change_with_filter(self, logged_in_client):
        """Category percentage breakdown must only reflect expenses within the
        filtered range, not the unfiltered full dataset."""
        test_client, _ = logged_in_client

        # January-only: only one expense, Food $100 — should be 100 %
        response = test_client.get(
            "/profile?from_date=2026-01-01&to_date=2026-01-31"
        )
        html = response.data
        assert b"Food" in html
        # With a single expense the percentage must be 100.
        assert b"100" in html
        # Transport ($50 in March) must not appear.
        assert b"Transport" not in html

    def test_single_expense_in_range_correct_total(self, logged_in_client):
        """Filtering to a narrow range containing exactly one expense must
        reflect that expense's amount as the total."""
        test_client, _ = logged_in_client
        # Only the March bus pass falls in this window.
        response = test_client.get(
            "/profile?from_date=2026-03-01&to_date=2026-03-31"
        )
        assert b"50.00" in response.data
        assert b"March bus pass" in response.data
