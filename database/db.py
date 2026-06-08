import sqlite3
import os
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "spendly.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            name          TEXT    NOT NULL,
            email         TEXT    UNIQUE NOT NULL,
            password_hash TEXT    NOT NULL,
            created_at    TEXT    DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users(id),
            amount      REAL    NOT NULL,
            category    TEXT    NOT NULL,
            date        TEXT    NOT NULL,
            description TEXT,
            created_at  TEXT    DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    conn.close()


def seed_db():
    conn = get_db()
    row = conn.execute("SELECT COUNT(*) FROM users").fetchone()
    if row[0] > 0:
        conn.close()
        return

    cursor = conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("Demo User", "demo@spendly.com", generate_password_hash("demo123", method="pbkdf2:sha256")),
    )
    user_id = cursor.lastrowid

    expenses = [
        (user_id, 42.50,  "Food",          "2026-06-01", "Grocery run"),
        (user_id, 15.00,  "Transport",     "2026-06-03", "Bus pass top-up"),
        (user_id, 120.00, "Bills",         "2026-06-05", "Electricity bill"),
        (user_id, 35.00,  "Health",        "2026-06-08", "Pharmacy"),
        (user_id, 25.00,  "Entertainment", "2026-06-10", "Cinema tickets"),
        (user_id, 89.99,  "Shopping",      "2026-06-14", "New shoes"),
        (user_id, 10.00,  "Other",         "2026-06-18", "Charity donation"),
        (user_id, 55.75,  "Food",          "2026-06-22", "Restaurant dinner"),
    ]
    conn.executemany(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        expenses,
    )
    conn.commit()
    conn.close()


def create_user(name, email, password_hash):
    conn = get_db()
    try:
        cursor = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, password_hash),
        )
        user_id = cursor.lastrowid
        conn.commit()
        return user_id
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def get_user_by_email(email):
    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE email = ?", (email,)
    ).fetchone()
    conn.close()
    return user


def get_user_by_id(user_id):
    conn = get_db()
    try:
        return conn.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    finally:
        conn.close()


def _date_filters(from_date, to_date):
    """Return (where_clause_fragment, params_list) for optional date bounds."""
    clauses, params = [], []
    if from_date:
        clauses.append("date >= ?")
        params.append(from_date)
    if to_date:
        clauses.append("date <= ?")
        params.append(to_date)
    fragment = (" AND " + " AND ".join(clauses)) if clauses else ""
    return fragment, params


def get_recent_expenses(user_id, limit=None, from_date=None, to_date=None):
    date_fragment, date_params = _date_filters(from_date, to_date)
    query = (
        "SELECT id, amount, category, date, description FROM expenses"
        " WHERE user_id = ?" + date_fragment + " ORDER BY date DESC"
    )
    params = (user_id, *date_params)
    if limit is not None:
        query += " LIMIT ?"
        params = (*params, limit)
    conn = get_db()
    try:
        return conn.execute(query, params).fetchall()
    finally:
        conn.close()


def get_expense_stats(user_id, from_date=None, to_date=None):
    date_fragment, date_params = _date_filters(from_date, to_date)
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT COALESCE(SUM(amount), 0.0) as total, COUNT(*) as cnt"
            " FROM expenses WHERE user_id = ?" + date_fragment,
            (user_id, *date_params),
        ).fetchone()
        total_spent = float(row["total"])
        transaction_count = int(row["cnt"])

        top_row = conn.execute(
            "SELECT category FROM expenses WHERE user_id = ?" + date_fragment
            + " GROUP BY category ORDER BY SUM(amount) DESC LIMIT 1",
            (user_id, *date_params),
        ).fetchone()
        top_category = top_row["category"] if top_row else None

        return {"total_spent": total_spent, "transaction_count": transaction_count, "top_category": top_category}
    finally:
        conn.close()


def get_category_totals(user_id, from_date=None, to_date=None):
    date_fragment, date_params = _date_filters(from_date, to_date)
    query = (
        "SELECT category, SUM(amount) as total FROM expenses"
        " WHERE user_id = ?" + date_fragment + " GROUP BY category ORDER BY total DESC"
    )
    conn = get_db()
    try:
        rows = conn.execute(query, (user_id, *date_params)).fetchall()
        if not rows:
            return []
        grand_total = sum(float(row["total"]) for row in rows)
        result = []
        for row in rows:
            row_total = float(row["total"])
            pct = int(round(row_total / grand_total * 100)) if grand_total else 0
            result.append({"name": row["category"], "total": row_total, "pct": pct})
        return result
    finally:
        conn.close()
