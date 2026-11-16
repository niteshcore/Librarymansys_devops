from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for

from . import models

bp = Blueprint("main", __name__)


def validate_book(data):
    """Returns (clean_data, None) if valid, or (None, error_message)."""
    title = str(data.get("title") or "").strip()
    author = str(data.get("author") or "").strip()
    isbn = str(data.get("isbn") or "").strip()

    if not title or not author or not isbn:
        return None, "Title, author and ISBN are required."

    try:
        copies = int(data.get("copies", 1))
    except (TypeError, ValueError):
        return None, "Copies must be a whole number."
    if copies < 1:
        return None, "Copies must be at least 1."

    return {"title": title, "author": author, "isbn": isbn, "copies": copies}, None


@bp.route("/health")
def health():
    # Used by Docker's healthcheck and the pipeline's smoke test
    return jsonify(status="ok")


# ---------- HTML pages ----------

@bp.route("/")
def index():
    query = request.args.get("q", "").strip()
    books = models.get_books(query)
    return render_template("index.html", books=books, query=query)


@bp.route("/add", methods=["GET", "POST"])
def add_book_page():
    if request.method == "POST":
        book, error = validate_book(request.form)
        if error:
            flash(error, "error")
            return render_template("add.html", form=request.form), 400
        if models.add_book(**book) is None:
            flash("A book with this ISBN already exists.", "error")
            return render_template("add.html", form=request.form), 409
        flash(f"Added '{book['title']}'.", "success")
        # Redirect after POST, so refreshing the page does not add the book twice
        return redirect(url_for("main.index"))
    return render_template("add.html", form={})


@bp.route("/books/<int:book_id>/issue", methods=["POST"])
def issue_book_page(book_id):
    if models.issue_book(book_id):
        flash("Book issued.", "success")
    else:
        flash("No copies available to issue.", "error")
    return redirect(url_for("main.index"))


@bp.route("/books/<int:book_id>/return", methods=["POST"])
def return_book_page(book_id):
    if models.return_book(book_id):
        flash("Book returned.", "success")
    else:
        flash("All copies of this book are already in the library.", "error")
    return redirect(url_for("main.index"))


@bp.route("/books/<int:book_id>/delete", methods=["POST"])
def delete_book_page(book_id):
    if models.delete_book(book_id):
        flash("Book deleted.", "success")
    else:
        flash("Book not found.", "error")
    return redirect(url_for("main.index"))


# ---------- JSON API ----------

@bp.route("/api/books", methods=["GET"])
def api_list_books():
    query = request.args.get("q", "").strip()
    return jsonify(models.get_books(query))


@bp.route("/api/books/<int:book_id>", methods=["GET"])
def api_get_book(book_id):
    book = models.get_book(book_id)
    if book is None:
        return jsonify(error="Book not found"), 404
    return jsonify(book)


@bp.route("/api/books", methods=["POST"])
def api_add_book():
    # silent=True returns None instead of raising an error for invalid JSON
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(error="Request body must be a JSON object"), 400
    book, error = validate_book(data)
    if error:
        return jsonify(error=error), 400
    book_id = models.add_book(**book)
    if book_id is None:
        return jsonify(error="A book with this ISBN already exists"), 409
    return jsonify(models.get_book(book_id)), 201


@bp.route("/api/books/<int:book_id>/issue", methods=["POST"])
def api_issue_book(book_id):
    if models.get_book(book_id) is None:
        return jsonify(error="Book not found"), 404
    if not models.issue_book(book_id):
        return jsonify(error="No copies available"), 400
    return jsonify(models.get_book(book_id))


@bp.route("/api/books/<int:book_id>/return", methods=["POST"])
def api_return_book(book_id):
    if models.get_book(book_id) is None:
        return jsonify(error="Book not found"), 404
    if not models.return_book(book_id):
        return jsonify(error="All copies are already returned"), 400
    return jsonify(models.get_book(book_id))


@bp.route("/api/books/<int:book_id>", methods=["DELETE"])
def api_delete_book(book_id):
    if not models.delete_book(book_id):
        return jsonify(error="Book not found"), 404
    return jsonify(message="Book deleted")
