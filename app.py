from flask import Flask, render_template, request, redirect, session
from datetime import datetime
import psycopg2
import os
from database import init_db, migrate_resources
from werkzeug.utils import secure_filename


app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret")

UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"pdf", "docx", "pptx", "png", "jpg", "jpeg"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def get_db():
    return psycopg2.connect(
        os.environ.get("DATABASE_URL"),
        sslmode="require"
    )


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS waitlist (
            id SERIAL PRIMARY KEY,
            email TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS news (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            date TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS faq (
            id SERIAL PRIMARY KEY,
            question TEXT NOT NULL,
            answer TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS resources (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            resource_type TEXT NOT NULL,
            url TEXT NOT NULL,
            description TEXT
        )
    """)

    conn.commit()
    conn.close()

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# ------------------ SHARED DATA ------------------

def get_total_members():
    try:
        conn = get_db()
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
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO waitlist (email) VALUES (%s)", (email,))
    conn.commit()
    conn.close()

# ------------------ ROUTES ------------------

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # SIMPLE ADMIN CREDENTIALS
        if (
            username == os.environ.get("ADMIN_USER")
            and password == os.environ.get("ADMIN_PASS")
        ):
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
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT question, answer FROM faq")
    faqs = cursor.fetchall()
    conn.close()

    return render_template("faq.html", faqs=faqs)

@app.route("/resources")
def resources():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT title, resource_type, url, description, category, updated_at
        FROM resources
        ORDER BY id DESC
    """)

    resources = cursor.fetchall()
    conn.close()

    return render_template("resources.html", resources=resources)

# ------------------ NEWS ------------------

@app.route("/news")
def news():
    conn = get_db()
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

    conn = get_db()
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

    conn = get_db()
    cursor = conn.cursor()

    # HANDLE NEW POST
    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]
        date = datetime.now().strftime("%b %d, %Y")

        cursor.execute(
            "INSERT INTO news (title, content, date) VALUES (%s, %s, %s)",
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

    conn = get_db()
    cursor = conn.cursor()

    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]

        cursor.execute(
            "UPDATE news SET title = %s, content = %s WHERE id = %s",
            (title, content, news_id)
        )
        conn.commit()
        conn.close()

        return redirect("/admin/news")

    cursor.execute("SELECT * FROM news WHERE id = %s", (news_id,))
    news = cursor.fetchone()
    conn.close()

    return render_template("edit_news.html", news=news)

@app.route("/admin/news/delete/<int:news_id>")
def delete_news(news_id):
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")
    
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM news WHERE id = %s", (news_id,))
    conn.commit()
    conn.close()

    return redirect("/admin/news")

@app.route("/admin/faq", methods=["GET", "POST"])
def admin_faq():
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    conn = get_db()
    cursor = conn.cursor()

    if request.method == "POST":
        question = request.form["question"]
        answer = request.form["answer"]

        cursor.execute(
            "INSERT INTO faq (question, answer) VALUES (%s, %s)",
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

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM faq WHERE id = %s", (faq_id,))
    conn.commit()
    conn.close()

    return redirect("/admin/faq")

@app.route("/admin/faq/edit/<int:faq_id>", methods=["GET", "POST"])
def edit_faq(faq_id):
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    conn = get_db()
    cursor = conn.cursor()

    if request.method == "POST":
        question = request.form["question"]
        answer = request.form["answer"]

        cursor.execute(
            "UPDATE faq SET question = %s, answer = %s WHERE id = %s",
            (question, answer, faq_id)
        )
        conn.commit()
        conn.close()
        return redirect("/admin/faq")

    cursor.execute(
        "SELECT id, question, answer FROM faq WHERE id = %s",
        (faq_id,)
    )
    faq = cursor.fetchone()
    conn.close()

    return render_template("edit_faq.html", faq=faq)

@app.route("/admin/resources", methods=["GET", "POST"])
def admin_resources():
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    conn = get_db()
    cursor = conn.cursor()

    if request.method == "POST":
    title = request.form["title"]
    resource_type = request.form["resource_type"]
    url = request.form["url"]
    description = request.form["description"]
    category = request.form["category"]
    updated_at = datetime.now().strftime("%b %d, %Y")

    cursor.execute(
        """
        INSERT INTO resources
        (title, resource_type, url, description, category, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (title, resource_type, url, description, category, updated_at)
    )
    conn.commit()

    cursor.execute(
        "SELECT id, title, resource_type, url, description FROM resources ORDER BY id DESC"
    )
    resources = cursor.fetchall()
    conn.close()

    return render_template("admin_resources.html", resources=resources)

@app.route("/admin/resources/edit/<int:resource_id>", methods=["GET", "POST"])
def edit_resource(resource_id):
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    conn = get_db()
    cursor = conn.cursor()

    if request.method == "POST":
        title = request.form["title"]
        resource_type = request.form["resource_type"]
        url = request.form["url"]
        description = request.form["description"]
        category = request.form["category"]
        updated_at = datetime.now().strftime("%Y-%m-%d")

        cursor.execute(
            """
            UPDATE resources
            SET title=%s,
                resource_type=%s,
                url=%s,
                description=%s,
                category=%s,
                updated_at=%s
            WHERE id=%s
            """,
            (title, resource_type, url, description, category, updated_at, resource_id)
        )

        conn.commit()
        conn.close()
        return redirect("/admin/resources")

    cursor.execute(
        """
        SELECT id, title, resource_type, url, description, category
        FROM resources
        WHERE id = %s
        """,
        (resource_id,)
    )
    resource = cursor.fetchone()
    conn.close()

    return render_template("edit_resource.html", resource=resource)


@app.route("/admin/resources/delete/<int:resource_id>")
def delete_resource(resource_id):
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM resources WHERE id = %s", (resource_id,))
    conn.commit()
    conn.close()

    return redirect("/admin/resources")



# ------------------ RUN APP ------------------

with app.app_context():
    init_db()
    migrate_resources()

if __name__ == "__main__":
    app.run()
