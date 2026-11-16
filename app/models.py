import sqlite3

from flask import current_app, g


def get_db():
    # One connection per request, stored on Flask's "g" object
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
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
    db = get_db()
    if search:
        # "?" placeholders pass values safely and prevent SQL injection
        pattern = f"%{search}%"
        rows = db.execute(
            "SELECT * FROM books WHERE title LIKE ? OR author LIKE ? ORDER BY title",
            (pattern, pattern),
        ).fetchall()
    else:
        rows = db.execute("SELECT * FROM books ORDER BY title").fetchall()
    return [dict(row) for row in rows]


def get_book(book_id):
    row = get_db().execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
    return dict(row) if row else None


def add_book(title, author, isbn, copies):
    db = get_db()
    try:
        cursor = db.execute(
            "INSERT INTO books (title, author, isbn, total_copies, available_copies) "
            "VALUES (?, ?, ?, ?, ?)",
            (title, author, isbn, copies, copies),
        )
    except sqlite3.IntegrityError:
        # ISBN is UNIQUE, so a duplicate ISBN ends up here
        return None
    db.commit()
    return cursor.lastrowid


def issue_book(book_id):
    # The WHERE condition means available copies can never go below 0
    db = get_db()
    cursor = db.execute(
        "UPDATE books SET available_copies = available_copies - 1 "
        "WHERE id = ? AND available_copies > 0",
        (book_id,),
    )
    db.commit()
    return cursor.rowcount == 1


def return_book(book_id):
    db = get_db()
    cursor = db.execute(
        "UPDATE books SET available_copies = available_copies + 1 "
        "WHERE id = ? AND available_copies < total_copies",
        (book_id,),
    )
    db.commit()
    return cursor.rowcount == 1


def delete_book(book_id):
    db = get_db()
    cursor = db.execute("DELETE FROM books WHERE id = ?", (book_id,))
    db.commit()
    return cursor.rowcount == 1
