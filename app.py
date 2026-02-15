from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
import recommender   # ✅ Import recommender.py safely

app = Flask(__name__)

# ✅ Strong secret key for sessions (Render needs stable key)
app.secret_key = "bookrec_super_secret_key_2026"

# ✅ Session settings for Render HTTPS
app.config["SESSION_COOKIE_SECURE"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"


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
    return redirect(url_for("login"))


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
            conn.close()
            return "User already exists! Try logging in."

        conn.close()
        return redirect(url_for("login"))

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
            return redirect(url_for("home"))
        else:
            return "Invalid credentials!"

    return render_template("login.html")


# ----------- HOME ----------- #
@app.route("/home")
def home():
    if "user" not in session:
        return redirect(url_for("login"))

    return render_template("home.html", user=session["user"])


# ----------- RECOMMEND FORM ----------- #
@app.route("/recommend", methods=["GET", "POST"])
def recommend():
    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        book_name = request.form["book"]

        print("📌 Book Entered:", book_name)

        # ✅ KNN Recommendation + Popularity fallback
        recommendations = recommender.recommend_books(book_name)

        print("✅ Recommendations Generated:", recommendations)

        return render_template("result.html", books=recommendations)

    return render_template("recommend.html")


# ----------- LOGOUT ----------- #
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------------- RUN SERVER ---------------- #
if __name__ == "__main__":
    app.run()
