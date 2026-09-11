from src.sso import session_from_oidc_user


def test_oidc_user_maps_to_provisioned_local_user(monkeypatch):
    class FakeDB:
        def get_user(self, username):
            return {"username": username, "role": "manager", "active": True}

    monkeypatch.setattr("src.sso.Database", FakeDB)
    user = {"email": "manager@example.com", "iss": "https://accounts.google.com"}
    session = session_from_oidc_user(user)

    assert session["username"] == "manager@example.com"
    assert session["role"] == "manager"
    assert "finance" in session["allowed_departments"]


def test_oidc_user_must_be_provisioned(monkeypatch):
    class FakeDB:
        def get_user(self, username):
            return None

    monkeypatch.setattr("src.sso.Database", FakeDB)

    try:
        session_from_oidc_user({"email": "unknown@example.com"})
    except ValueError as exc:
        assert "not provisioned" in str(exc)
    else:
        raise AssertionError("Unprovisioned OIDC user should be rejected")
