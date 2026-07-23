"""
Unit tests for authentication security helpers.
"""

import pytest
from app.auth.security import generate_api_key, hash_api_key


def test_api_key_has_prefix():
    key = generate_api_key()
    assert key.startswith("ad_")


def test_api_key_generation():
    key = generate_api_key()
    assert len(key) > 10


def test_api_key_uniqueness():
    """Two generated keys must always be different."""
    keys = {generate_api_key() for _ in range(50)}
    assert len(keys) == 50


def test_api_key_hashing():
    """Same key must always produce the same hash."""
    key = generate_api_key()
    assert hash_api_key(key) == hash_api_key(key)


def test_different_keys_different_hashes():
    key1 = generate_api_key()
    key2 = generate_api_key()
    assert hash_api_key(key1) != hash_api_key(key2)


def test_hash_is_hex_string():
    """SHA-256 hash must be a 64-char hex string."""
    key = generate_api_key()
    h = hash_api_key(key)
    assert len(h) == 64
    assert all(c in "0123456789abcdef" for c in h)


def test_api_key_min_entropy():
    """Key must be at least 40 chars to ensure sufficient entropy."""
    key = generate_api_key()
    assert len(key) >= 40
