from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect("waitlist.db")
    cursor = conn.cursor()

    # WAITLIST TABLE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS waitlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL
        )
    """)

    # NEWS TABLE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            date TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()

def init_db():
    conn = sqlite3.connect("waitlist.db")
    cursor = conn.cursor()

    # FAQ table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS faq (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            answer TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


app = Flask(__name__)
app.secret_key = "8f3k9aL2xQ7mP4Zs9D1WcR0Y"

init_db()

# ------------------ SHARED DATA ------------------

def get_total_members():
    try:
        conn = sqlite3.connect("waitlist.db")
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM waitlist")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except:
        return 0

@app.context_processor
def inject_global_data():
    return {
        "total_members": get_total_members()
    }

# ------------------ DATABASE HELPERS ------------------

def save_email(email):
    conn = sqlite3.connect("waitlist.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO waitlist (email) VALUES (?)", (email,))
    conn.commit()
    conn.close()

# ------------------ ROUTES ------------------

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # SIMPLE ADMIN CREDENTIALS
        if username == "admin" and password == "password123":
            session["admin_logged_in"] = True
            return redirect("/admin/news")
        else:
            return render_template(
                "admin_login.html",
                error="Invalid login details"
            )

    return render_template("admin_login.html")

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    return redirect("/admin/login")

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/community")
def community():
    return render_template("community.html")

@app.route("/faq")
def faq():
    conn = sqlite3.connect("waitlist.db")
    cursor = conn.cursor()
    cursor.execute("SELECT question, answer FROM faq")
    faqs = cursor.fetchall()
    conn.close()

    return render_template("faq.html", faqs=faqs)

# ------------------ NEWS ------------------

@app.route("/news")
def news():
    conn = sqlite3.connect("waitlist.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, content, date FROM news ORDER BY id DESC")
    news_items = cursor.fetchall()
    conn.close()

    return render_template("news.html", news_items=news_items)

# ------------------ WAITLIST ------------------

@app.route("/join", methods=["POST"])
def join():
    email = request.form["email"]
    save_email(email)
    return redirect("/")

@app.route("/admin/waitlist")
def view_waitlist():
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    conn = sqlite3.connect("waitlist.db")
    cursor = conn.cursor()
    cursor.execute("SELECT email FROM waitlist")
    emails = cursor.fetchall()
    conn.close()

    return render_template("waitlist.html", emails=emails)


# ------------------ ADMIN NEWS ------------------

@app.route("/admin/news", methods=["GET", "POST"])
def admin_news():
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    conn = sqlite3.connect("waitlist.db")
    cursor = conn.cursor()

    # HANDLE NEW POST
    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]
        date = datetime.now().strftime("%b %d, %Y")

        cursor.execute(
            "INSERT INTO news (title, content, date) VALUES (?, ?, ?)",
            (title, content, date)
        )
        conn.commit()

    # FETCH ALL NEWS FOR ADMIN VIEW
    cursor.execute("SELECT id, title, content, date FROM news ORDER BY id DESC")
    news_items = cursor.fetchall()

    conn.close()

    return render_template("admin_news.html", news_items=news_items)

@app.route("/admin/news/edit/<int:news_id>", methods=["GET", "POST"])
def edit_news(news_id):
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    conn = sqlite3.connect("waitlist.db")
    cursor = conn.cursor()

    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]

        cursor.execute(
            "UPDATE news SET title = ?, content = ? WHERE id = ?",
            (title, content, news_id)
        )
        conn.commit()
        conn.close()

        return redirect("/news")

    cursor.execute("SELECT * FROM news WHERE id = ?", (news_id,))
    news = cursor.fetchone()
    conn.close()

    return render_template("edit_news.html", news=news)

@app.route("/admin/news/delete/<int:news_id>")
def delete_news(news_id):
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")
    
    conn = sqlite3.connect("waitlist.db")
    cursor = conn.cursor()

    cursor.execute("DELETE FROM news WHERE id = ?", (news_id,))
    conn.commit()
    conn.close()

    return redirect("/news")

@app.route("/admin/faq", methods=["GET", "POST"])
def admin_faq():
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    conn = sqlite3.connect("waitlist.db")
    cursor = conn.cursor()

    if request.method == "POST":
        question = request.form["question"]
        answer = request.form["answer"]

        cursor.execute(
            "INSERT INTO faq (question, answer) VALUES (?, ?)",
            (question, answer)
        )
        conn.commit()

    cursor.execute("SELECT id, question, answer FROM faq")
    faqs = cursor.fetchall()
    conn.close()

    return render_template("admin_faq.html", faqs=faqs)

@app.route("/admin/faq/delete/<int:faq_id>")
def delete_faq(faq_id):
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    conn = sqlite3.connect("waitlist.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM faq WHERE id = ?", (faq_id,))
    conn.commit()
    conn.close()

    return redirect("/admin/faq")

@app.route("/admin/faq/edit/<int:faq_id>", methods=["GET", "POST"])
def edit_faq(faq_id):
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    conn = sqlite3.connect("waitlist.db")
    cursor = conn.cursor()

    if request.method == "POST":
        question = request.form["question"]
        answer = request.form["answer"]

        cursor.execute(
            "UPDATE faq SET question = ?, answer = ? WHERE id = ?",
            (question, answer, faq_id)
        )
        conn.commit()
        conn.close()
        return redirect("/admin/faq")

    cursor.execute(
        "SELECT id, question, answer FROM faq WHERE id = ?",
        (faq_id,)
    )
    faq = cursor.fetchone()
    conn.close()

    return render_template("edit_faq.html", faq=faq)

# ------------------ RUN APP ------------------

if __name__ == "__main__":
    app.run()
