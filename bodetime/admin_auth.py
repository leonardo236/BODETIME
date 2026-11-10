"""Clave local de administrador para operaciones que modifican el catálogo."""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets

from dotenv import dotenv_values, set_key

from .config import APP_CONFIG_DIR, ENV_FILE


ADMIN_HASH_KEY = "BODETIME_ADMIN_PASSWORD_HASH"
PBKDF2_ITERATIONS = 600_000


def _stored_password_hash() -> str:
    if not ENV_FILE.is_file():
        return ""
    return (dotenv_values(ENV_FILE).get(ADMIN_HASH_KEY) or "").strip()


def has_admin_password() -> bool:
    return bool(_stored_password_hash())


def make_password_hash(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password_hash(password: str, stored_hash: str) -> bool:
    try:
        algorithm, rounds_text, salt_hex, expected_hex = stored_hash.split("$", 3)
        rounds = int(rounds_text)
        if algorithm != "pbkdf2_sha256" or not 100_000 <= rounds <= 2_000_000:
            return False
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(expected_hex)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, rounds)
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def verify_admin_password(password: str) -> bool:
    return verify_password_hash(password, _stored_password_hash())


def save_admin_password(password: str) -> None:
    if len(password) < 12:
        raise ValueError("La clave de administrador debe tener al menos 12 caracteres.")
    if not ENV_FILE.exists():
        APP_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        ENV_FILE.touch()
    password_hash = make_password_hash(password)
    set_key(str(ENV_FILE), ADMIN_HASH_KEY, password_hash, quote_mode="never")


def is_local_system_admin() -> bool:
    """Comprueba elevación local para el primer registro del administrador."""
    if os.name == "nt":
        try:
            import ctypes

            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except (AttributeError, OSError):
            return False
    return hasattr(os, "geteuid") and os.geteuid() == 0
