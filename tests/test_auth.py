import bcrypt
from contextlib import contextmanager

import src.auth as auth


def _make_get_db_connection(row):
    """Return a contextmanager that yields a fake connection/cursor.

    `row` will be returned by cursor.fetchone().
    """
    @contextmanager
    def _ctx():
        class DummyCursor:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def execute(self, *args, **kwargs):
                pass

            def fetchone(self):
                return row

        class DummyConn:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def cursor(self):
                return DummyCursor()

        yield DummyConn()

    return _ctx


def test_auth_user_not_found(monkeypatch):
    monkeypatch.setattr(auth.db, "get_db_connection", _make_get_db_connection(None))
    assert auth.authenticate("nouser", "pw") is None


def test_auth_with_bcrypt_hash(monkeypatch):
    password = "s3cr3t"
    pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

    row = (1, "alice", "admin", pw_hash)
    monkeypatch.setattr(auth.db, "get_db_connection", _make_get_db_connection(row))

    res = auth.authenticate("alice", password)
    assert res == {"user_id": 1, "username": "alice", "role": "admin"}


def test_auth_legacy_plaintext_password(monkeypatch):
    password = "legacy123"
    row = (2, "legacy", "staff", password)  # legacy plaintext stored in DB
    monkeypatch.setattr(auth.db, "get_db_connection", _make_get_db_connection(row))

    res = auth.authenticate("legacy", password)
    assert res == {"user_id": 2, "username": "legacy", "role": "staff"}
