import pytest

from app import create_app


@pytest.fixture
def client(tmp_path):
    # Each test gets a fresh database in a temporary folder, so tests never touch real data
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "test.db")})
    return app.test_client()


def add_sample_book(client, title="Clean Code", author="Robert Martin", isbn="111", copies=2):
    return client.post(
        "/api/books",
        json={"title": title, "author": author, "isbn": isbn, "copies": copies},
    )


def test_health_returns_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_add_book(client):
    response = add_sample_book(client)
    assert response.status_code == 201
    book = response.get_json()
    assert book["title"] == "Clean Code"
    assert book["total_copies"] == 2
    assert book["available_copies"] == 2


def test_list_books(client):
    add_sample_book(client, isbn="111")
    add_sample_book(client, title="Dune", author="Frank Herbert", isbn="222")
    response = client.get("/api/books")
    assert response.status_code == 200
    assert len(response.get_json()) == 2


def test_get_single_book(client):
    book_id = add_sample_book(client).get_json()["id"]
    response = client.get(f"/api/books/{book_id}")
    assert response.status_code == 200
    assert response.get_json()["isbn"] == "111"


def test_search_by_title_and_author(client):
    add_sample_book(client, title="Clean Code", author="Robert Martin", isbn="111")
    add_sample_book(client, title="Dune", author="Frank Herbert", isbn="222")

    by_title = client.get("/api/books?q=dune").get_json()
    assert [b["title"] for b in by_title] == ["Dune"]

    by_author = client.get("/api/books?q=martin").get_json()
    assert [b["title"] for b in by_author] == ["Clean Code"]

    assert client.get("/api/books?q=harry").get_json() == []


def test_issue_book_reduces_available_copies(client):
    book_id = add_sample_book(client, copies=2).get_json()["id"]
    response = client.post(f"/api/books/{book_id}/issue")
    assert response.status_code == 200
    assert response.get_json()["available_copies"] == 1


def test_cannot_issue_when_no_copies_left(client):
    book_id = add_sample_book(client, copies=1).get_json()["id"]
    client.post(f"/api/books/{book_id}/issue")
    response = client.post(f"/api/books/{book_id}/issue")
    assert response.status_code == 400
    assert client.get(f"/api/books/{book_id}").get_json()["available_copies"] == 0


def test_return_book_increases_available_copies(client):
    book_id = add_sample_book(client, copies=2).get_json()["id"]
    client.post(f"/api/books/{book_id}/issue")
    response = client.post(f"/api/books/{book_id}/return")
    assert response.status_code == 200
    assert response.get_json()["available_copies"] == 2


def test_cannot_return_when_all_copies_in_library(client):
    book_id = add_sample_book(client, copies=2).get_json()["id"]
    response = client.post(f"/api/books/{book_id}/return")
    assert response.status_code == 400
    assert client.get(f"/api/books/{book_id}").get_json()["available_copies"] == 2


def test_delete_book(client):
    book_id = add_sample_book(client).get_json()["id"]
    response = client.delete(f"/api/books/{book_id}")
    assert response.status_code == 200
    assert client.get(f"/api/books/{book_id}").status_code == 404


def test_add_book_with_missing_fields_fails(client):
    response = client.post("/api/books", json={"author": "Someone", "isbn": "999"})
    assert response.status_code == 400
    assert "required" in response.get_json()["error"]


def test_add_book_with_invalid_copies_fails(client):
    assert add_sample_book(client, copies=0).status_code == 400
    assert add_sample_book(client, copies="abc").status_code == 400


def test_add_book_with_duplicate_isbn_fails(client):
    add_sample_book(client, isbn="111")
    response = add_sample_book(client, title="Another Book", isbn="111")
    assert response.status_code == 409


def test_add_book_with_non_json_body_fails(client):
    response = client.post("/api/books", data="not json")
    assert response.status_code == 400


def test_unknown_book_returns_404(client):
    assert client.get("/api/books/999").status_code == 404
    assert client.post("/api/books/999/issue").status_code == 404
    assert client.post("/api/books/999/return").status_code == 404
    assert client.delete("/api/books/999").status_code == 404


def test_home_page_lists_books(client):
    add_sample_book(client)
    response = client.get("/")
    assert response.status_code == 200
    assert b"Clean Code" in response.data
    assert b"Available" in response.data


def test_add_book_through_html_form(client):
    assert client.get("/add").status_code == 200
    response = client.post(
        "/add",
        data={"title": "Dune", "author": "Frank Herbert", "isbn": "222", "copies": "3"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Dune" in response.data

    bad = client.post("/add", data={"title": "", "author": "X", "isbn": "333", "copies": "1"})
    assert bad.status_code == 400


def test_issue_return_delete_buttons(client):
    book_id = add_sample_book(client, copies=1).get_json()["id"]

    response = client.post(f"/books/{book_id}/issue", follow_redirects=True)
    assert b"Book issued." in response.data

    response = client.post(f"/books/{book_id}/return", follow_redirects=True)
    assert b"Book returned." in response.data

    response = client.post(f"/books/{book_id}/delete", follow_redirects=True)
    assert b"Book deleted." in response.data
    assert client.get(f"/api/books/{book_id}").status_code == 404
