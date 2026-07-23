from app.auth.security import generate_api_key, hash_api_key


def test_api_key_generation():
    key = generate_api_key()
    assert key.startswith("ad_")
    assert len(key) > 30


def test_api_key_hashing():
    key = "ad_test_key_123"
    hash1 = hash_api_key(key)
    hash2 = hash_api_key(key)
    assert hash1 == hash2
    assert hash1 != hash_api_key("ad_different_key")
