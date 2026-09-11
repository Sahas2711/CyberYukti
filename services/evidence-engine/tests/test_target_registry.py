"""Tests for Target Registry module."""

from validator.target_registry import get_registered_asset_ids, is_port_allowed, resolve_target


def test_resolve_known_targets():
    target = resolve_target("shop-api-01")
    assert target is not None
    assert target["host"] == "127.0.0.1"
    assert 8080 in target["allowed_ports"]

    patched_target = resolve_target("shop-api-01-patched")
    assert patched_target is not None
    assert patched_target["lab_env"] == "patched"


def test_resolve_unknown_targets_returns_none():
    assert resolve_target("unknown-asset-99") is None
    assert resolve_target("arbitrary.evil.domain.com") is None
    assert resolve_target("") is None
    assert resolve_target(None) is None


def test_port_whitelist_check():
    # Allowed ports on shop-api-01 are [8080, 8081]
    assert is_port_allowed("shop-api-01", 8080) is True
    assert is_port_allowed("shop-api-01", 8081) is True

    # Disallowed ports
    assert is_port_allowed("shop-api-01", 22) is False
    assert is_port_allowed("shop-api-01", 443) is False
    assert is_port_allowed("shop-api-01", 3306) is False

    # Port on unregistered asset
    assert is_port_allowed("nonexistent-asset", 8080) is False

    # Invalid port formats
    assert is_port_allowed("shop-api-01", "invalid") is False


def test_registered_asset_list():
    assets = get_registered_asset_ids()
    assert "shop-api-01" in assets
    assert "shop-api-01-patched" in assets
