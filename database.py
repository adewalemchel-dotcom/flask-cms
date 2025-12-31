import psycopg2
import os

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
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS news (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            date TEXT NOT NULL
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS faq (
            id SERIAL PRIMARY KEY,
            question TEXT NOT NULL,
            answer TEXT NOT NULL
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS resources (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            resource_type TEXT NOT NULL,
            url TEXT NOT NULL,
            description TEXT,
            category TEXT,
            updated_at TEXT
        );
    """)

    conn.commit()
    cursor.close()
    conn.close()

def migrate_resources():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        ALTER TABLE resources
        ADD COLUMN IF NOT EXISTS category TEXT;
    """)

    cursor.execute("""
        ALTER TABLE resources
        ADD COLUMN IF NOT EXISTS updated_at TEXT;
    """)

    conn.commit()
    cursor.close()
    conn.close()

