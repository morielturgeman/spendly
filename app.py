import os
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import get_db, init_db, seed_db, create_user, get_user_by_email

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


@app.route("/profile")
def profile():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    user = {
        "name": "Alex Johnson",
        "email": "alex@example.com",
        "initials": "AJ",
        "member_since": "January 2024",
    }

    stats = {
        "total_spent": "$3,248.50",
        "transaction_count": 47,
        "top_category": "Food & Dining",
    }

    transactions = [
        {"date": "Jun 3, 2026",  "description": "Whole Foods Market",  "category": "Groceries",     "amount": "-$84.32"},
        {"date": "Jun 2, 2026",  "description": "Netflix Subscription", "category": "Entertainment", "amount": "-$15.99"},
        {"date": "Jun 1, 2026",  "description": "Shell Gas Station",    "category": "Transport",     "amount": "-$52.10"},
        {"date": "May 30, 2026", "description": "Chipotle",             "category": "Food & Dining", "amount": "-$13.45"},
        {"date": "May 28, 2026", "description": "Amazon Prime",         "category": "Shopping",      "amount": "-$139.00"},
    ]

    # Ordered by amount desc so cls 1=most spent (hottest color) → 5=least
    categories = [
        {"name": "Shopping",      "total": "$861.00", "pct": 26, "cls": "cat-1"},
        {"name": "Food & Dining", "total": "$842.30", "pct": 26, "cls": "cat-2"},
        {"name": "Groceries",     "total": "$634.80", "pct": 20, "cls": "cat-3"},
        {"name": "Transport",     "total": "$512.40", "pct": 16, "cls": "cat-4"},
        {"name": "Entertainment", "total": "$398.00", "pct": 12, "cls": "cat-5"},
    ]

    return render_template("profile.html", user=user, stats=stats,
                           transactions=transactions, categories=categories)


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
