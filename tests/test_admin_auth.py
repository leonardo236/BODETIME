from bodetime import admin_auth
from bodetime.admin_auth import make_password_hash, verify_password_hash


def test_admin_password_hash_matches_only_the_original_password():
    password = "Clave-segura-para-admin-2026"
    stored_hash = make_password_hash(password)
    assert password not in stored_hash
    assert verify_password_hash(password, stored_hash)
    assert not verify_password_hash("otra-clave", stored_hash)


def test_invalid_or_tampered_admin_hash_is_rejected():
    assert not verify_password_hash("password", "")
    assert not verify_password_hash("password", "pbkdf2_sha256$999999999$00$00")
    assert not verify_password_hash("password", "not-a-hash")


def test_admin_hash_is_read_from_private_env_file_not_process_environment(monkeypatch, tmp_path):
    password = "Clave-segura-para-admin-2026"
    monkeypatch.setattr(admin_auth, "ENV_FILE", tmp_path / ".env")
    admin_auth.save_admin_password(password)
    monkeypatch.setenv(admin_auth.ADMIN_HASH_KEY, make_password_hash("forged-environment-key"))
    assert admin_auth.has_admin_password()
    assert admin_auth.verify_admin_password(password)
    assert not admin_auth.verify_admin_password("forged-environment-key")
