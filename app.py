import os
from flask import Flask, render_template, request, redirect, url_for, session, abort
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, timedelta
from database.db import (get_db, init_db, seed_db, create_user, get_user_by_email,
                         get_user_by_id, get_recent_expenses, get_expense_stats,
                         get_category_totals)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key')

with app.app_context():
    init_db()
    seed_db()


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not name or not email or not password:
            return render_template("register.html", error="All fields are required.")
        confirm_password = request.form.get("confirm_password", "")
        if len(password) < 8:
            return render_template("register.html", error="Password must be at least 8 characters.")
        if password != confirm_password:
            return render_template("register.html", error="Passwords do not match.")
        if get_user_by_email(email):
            return render_template("register.html", error="An account with that email already exists.")

        user_id = create_user(name, email, generate_password_hash(password, method='pbkdf2:sha256'))
        if user_id is None:
            return render_template("register.html", error="An account with that email already exists.")
        session["user_id"] = user_id
        session["user_name"] = name
        return redirect(url_for("profile"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        user = get_user_by_email(email)
        if not user or not check_password_hash(user["password_hash"], password):
            return render_template("login.html", error="Invalid email or password.")

        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        return redirect(url_for("profile"))

    return render_template("login.html")


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/dashboard")
def dashboard():
    return "Dashboard — coming in Step 5"


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))


def _parse_date(value):
    """Return a validated YYYY-MM-DD string or None."""
    if not value:
        return None
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return value
    except ValueError:
        return None


def _compute_presets():
    today = date.today()
    first_of_month = today.replace(day=1)
    return {
        "this_month":    (first_of_month.isoformat(), today.isoformat()),
        "last_30":       ((today - timedelta(days=30)).isoformat(), today.isoformat()),
        "last_3_months": ((today - timedelta(days=90)).isoformat(), today.isoformat()),
        "all_time":      (None, None),
    }


def _fmt_display_date(d):
    return datetime.strptime(d, "%Y-%m-%d").strftime("%b %-d, %Y") if d else None


@app.route("/profile")
def profile():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    user_id = session["user_id"]
    user_row = get_user_by_id(user_id)
    if user_row is None:
        abort(404)

    created_dt = datetime.strptime(user_row["created_at"][:10], "%Y-%m-%d")
    member_since = created_dt.strftime("%B %Y")
    initials = "".join(p[0].upper() for p in user_row["name"].split()[:2])

    user = {
        "name": user_row["name"],
        "email": user_row["email"],
        "initials": initials,
        "member_since": member_since,
    }

    from_date = _parse_date(request.args.get("from_date"))
    to_date = _parse_date(request.args.get("to_date"))

    presets = _compute_presets()
    active_preset = "custom"
    if not from_date and not to_date:
        active_preset = "all_time"
    else:
        for key, (p_from, p_to) in presets.items():
            if from_date == p_from and to_date == p_to:
                active_preset = key
                break

    preset_urls = {
        key: url_for("profile", from_date=p_from, to_date=p_to)
        for key, (p_from, p_to) in presets.items()
    }

    if from_date or to_date:
        range_label = "{} – {}".format(_fmt_display_date(from_date) or "…", _fmt_display_date(to_date) or "…")
    else:
        range_label = "All time"

    stats_raw = get_expense_stats(user_id, from_date=from_date, to_date=to_date)
    stats = {
        "total_spent": "${:,.2f}".format(stats_raw["total_spent"]),
        "transaction_count": stats_raw["transaction_count"],
        "top_category": stats_raw["top_category"],
    }

    rows = get_recent_expenses(user_id, from_date=from_date, to_date=to_date)
    transactions = [
        {
            "date": datetime.strptime(row["date"], "%Y-%m-%d").strftime("%b %-d, %Y"),
            "description": row["description"] or "",
            "category": row["category"],
            "amount": "-${:,.2f}".format(row["amount"]),
        }
        for row in rows
    ]

    cats_raw = get_category_totals(user_id, from_date=from_date, to_date=to_date)
    categories = [
        {
            "name": cat["name"],
            "total": "${:,.2f}".format(cat["total"]),
            "pct": cat["pct"],
            "cls": "cat-{}".format(i + 1),
        }
        for i, cat in enumerate(cats_raw[:5])
    ]

    return render_template(
        "profile.html",
        user=user,
        stats=stats,
        transactions=transactions,
        categories=categories,
        from_date=from_date,
        to_date=to_date,
        active_preset=active_preset,
        preset_urls=preset_urls,
        range_label=range_label,
    )


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5001)
