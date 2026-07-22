from __future__ import annotations

from pwdlib import PasswordHash


# Configure the password hasher.
# pwdlib currently recommends Argon2 as the default algorithm.
_password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """
    Hash a plaintext password.

    Args:
        password: User's plaintext password.

    Returns:
        Secure Argon2 hash.
    """
    return _password_hash.hash(password)


def verify_password(
    plain_password: str,
    password_hash: str,
) -> bool:
    """
    Verify a plaintext password against its stored hash.

    Args:
        plain_password: Password supplied by the user.
        password_hash: Stored password hash.

    Returns:
        True if the password is valid.
    """
    return _password_hash.verify(
        plain_password,
        password_hash,
    )


def needs_rehash(password_hash: str) -> bool:
    """
    Determine whether an existing password hash should be upgraded.

    This allows automatic migration to stronger hashing parameters
    without forcing users to reset their passwords.
    """
    return _password_hash.needs_rehash(password_hash)