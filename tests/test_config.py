from fastapi.testclient import TestClient

from config import build_config, coerce
from main import app

client = TestClient(app)


def test_coerce_bool_values():
    for truthy in ["true", "1", "yes", "ON", " True "]:
        assert coerce("debug", truthy) is True
    for falsy in ["false", "0", "no", "off", "anything-else"]:
        assert coerce("debug", falsy) is False


def test_cli_override_beats_everything(monkeypatch):
    monkeypatch.setenv("APP_WORKERS", "3")
    config = build_config({"workers": "5"})
    assert config["workers"] == 5


def test_endpoint_masks_api_key():
    response = client.get("/effective-config")
    assert response.status_code == 200
    assert response.json()["api_key"] == "****"


def test_endpoint_applies_set_overrides():
    response = client.get("/effective-config?set=port=9000&set=debug=true")
    data = response.json()
    assert data["port"] == 9000
    assert data["debug"] is True


def test_unknown_key_returns_400():
    response = client.get("/effective-config?set=prot=9000")
    assert response.status_code == 400
