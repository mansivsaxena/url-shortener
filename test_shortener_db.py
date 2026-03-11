from datetime import datetime, timedelta, timezone

import pytest

from models import URL, User, db
from url_shortener_service import create_app


@pytest.fixture()
def app(tmp_path):
    db_path = tmp_path / "shortener.db"
    app = create_app()
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["TESTING"] = True

    with app.app_context():
        db.drop_all()
        db.create_all()
        db.session.add_all(
            [
                User(username="alice", salt=b"salt-a", pw_hash=b"hash-a"),
                User(username="bob", salt=b"salt-b", pw_hash=b"hash-b"),
            ]
        )
        db.session.commit()

    yield app


@pytest.fixture()
def client(app):
    return app.test_client()


def auth_as(monkeypatch, username):
    monkeypatch.setattr(
        "url_shortener_service.routes.require_authenticated_user",
        lambda req: (username, None),
    )


def test_health_and_readiness(client):
    assert client.get("/healthz").status_code == 200
    assert client.get("/readyz").status_code == 200


def test_url_persists_in_database(app, client, monkeypatch):
    auth_as(monkeypatch, "alice")
    response = client.post("/", json={"value": "https://example.com/persist"})
    short_id = response.get_json()["id"]

    restarted_app = create_app()
    restarted_app.config["SQLALCHEMY_DATABASE_URI"] = app.config["SQLALCHEMY_DATABASE_URI"]
    restarted_app.config["TESTING"] = True
    restarted_client = restarted_app.test_client()

    auth_as(monkeypatch, "alice")
    response = restarted_client.get("/")
    assert response.status_code == 200
    assert response.get_json()["value"] == {short_id: "https://example.com/persist"}


def test_owner_isolation(client, monkeypatch):
    auth_as(monkeypatch, "alice")
    response = client.post("/", json={"value": "https://example.com/alice"})
    short_id = response.get_json()["id"]

    auth_as(monkeypatch, "bob")
    assert client.put(f"/{short_id}", json={"url": "https://example.com/hijack"}).status_code == 403
    assert client.delete(f"/{short_id}").status_code == 403


def test_expired_url_behaves_as_missing(app, client, monkeypatch):
    auth_as(monkeypatch, "alice")
    expires_at = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
    response = client.post(
        "/",
        json={"value": "https://example.com/expired", "expires_at": expires_at},
    )
    short_id = response.get_json()["id"]

    assert client.get(f"/{short_id}").status_code == 404

    with app.app_context():
        assert URL.query.filter_by(short_code=short_id).first() is None
