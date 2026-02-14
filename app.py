from flask import Flask, render_template, request, redirect, session
import sqlite3
import recommender   # ✅ safer import (no ImportError)

app = Flask(__name__)
app.secret_key = "supersecretkey"


# ---------------- DATABASE SETUP ---------------- #
def init_db():
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            password TEXT
        )
    """)
    conn.commit()
    conn.close()


init_db()


# ---------------- ROUTES ---------------- #

@app.route("/")
def index():
    return redirect("/login")   # ✅ Correct route


# ----------- SIGNUP ----------- #
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cur = conn.cursor()

        try:
            cur.execute(
                "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                (name, email, password)
            )
            conn.commit()
        except:
            return "User already exists!"

        conn.close()
        return redirect("/login")

    return render_template("signup.html")


# ----------- LOGIN ----------- #
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM users WHERE email=? AND password=?",
            (email, password)
        )
        user = cur.fetchone()
        conn.close()

        if user:
            session["user"] = user[1]
            return redirect("/home")
        else:
            return "Invalid credentials!"

    return render_template("login.html")


# ----------- HOME ----------- #
@app.route("/home")
def home():
    if "user" not in session:
        return redirect("/login")

    return render_template("home.html", user=session["user"])


# ----------- RECOMMEND FORM ----------- #
@app.route("/recommend", methods=["GET", "POST"])
def recommend():
    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":
        book_name = request.form["book"]

        # ✅ KNN Recommendation + Popularity fallback
        recommendations = recommender.recommend_books(book_name)

        return render_template("result.html", books=recommendations)

    return render_template("recommend.html")



# ----------- LOGOUT ----------- #
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ---------------- RUN SERVER ---------------- #
if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
