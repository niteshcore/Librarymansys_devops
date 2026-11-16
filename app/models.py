"""Database helpers: every SQL query for the books table lives in this file."""
import sqlite3

from flask import current_app, g


def get_db():
    # Open one connection per request and keep it on Flask's "g" object
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        # Lets us read columns by name, e.g. row["title"]
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(exception=None):
    # Flask calls this at the end of each request to close the connection
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    # IF NOT EXISTS makes this safe to run every time the app starts
    db = get_db()
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            isbn TEXT NOT NULL UNIQUE,
            total_copies INTEGER NOT NULL,
            available_copies INTEGER NOT NULL
        )
        """
    )
    db.commit()


def get_books(search=None):
    # Return all books, or only books whose title or author contains the search text
    db = get_db()
    if search:
        # "?" placeholders let SQLite insert values safely (prevents SQL injection)
        pattern = f"%{search}%"
        rows = db.execute(
            "SELECT * FROM books WHERE title LIKE ? OR author LIKE ? ORDER BY title",
            (pattern, pattern),
        ).fetchall()
    else:
        rows = db.execute("SELECT * FROM books ORDER BY title").fetchall()
    # Convert rows to plain dicts so they can be turned into JSON
    return [dict(row) for row in rows]


def get_book(book_id):
    # Return one book as a dict, or None if the id does not exist
    row = get_db().execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
    return dict(row) if row else None


def add_book(title, author, isbn, copies):
    # A new book starts with all of its copies available
    db = get_db()
    try:
        cursor = db.execute(
            "INSERT INTO books (title, author, isbn, total_copies, available_copies) "
            "VALUES (?, ?, ?, ?, ?)",
            (title, author, isbn, copies, copies),
        )
    except sqlite3.IntegrityError:
        # The UNIQUE rule on isbn failed: a book with this ISBN already exists
        return None
    db.commit()
    return cursor.lastrowid


def issue_book(book_id):
    # Take one copy out, but only if at least one copy is available
    db = get_db()
    cursor = db.execute(
        "UPDATE books SET available_copies = available_copies - 1 "
        "WHERE id = ? AND available_copies > 0",
        (book_id,),
    )
    db.commit()
    # rowcount is 1 if a row was updated, 0 if no copy was available
    return cursor.rowcount == 1


def return_book(book_id):
    # Put one copy back, but only if some copies are currently issued
    db = get_db()
    cursor = db.execute(
        "UPDATE books SET available_copies = available_copies + 1 "
        "WHERE id = ? AND available_copies < total_copies",
        (book_id,),
    )
    db.commit()
    return cursor.rowcount == 1


def delete_book(book_id):
    # Remove the book; returns True if something was deleted
    db = get_db()
    cursor = db.execute("DELETE FROM books WHERE id = ?", (book_id,))
    db.commit()
    return cursor.rowcount == 1
