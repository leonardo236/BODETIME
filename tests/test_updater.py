import hashlib
import io
import json
from pathlib import Path
from threading import Event

import pytest

from bodetime import updater
from bodetime.updater import ReleaseInfo, UpdateCancelled, UpdateError, download_update, get_latest_release, is_newer_version


class FakeResponse(io.BytesIO):
    def __init__(self, content: bytes, url: str, headers: dict[str, str] | None = None):
        super().__init__(content)
        self._url = url
        self.headers = headers or {}

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.close()

    def geturl(self):
        return self._url


def test_version_check_compares_numeric_parts_not_strings():
    assert is_newer_version("1.0.10", "1.0.9")
    assert not is_newer_version("1.0.3", "1.0.4")
    with pytest.raises(UpdateError):
        is_newer_version("latest", "1.0.4")


def test_release_metadata_requires_canonical_installer_and_sha256(monkeypatch):
    payload = {
        "tag_name": "v1.0.5",
        "draft": False,
        "prerelease": False,
        "assets": [{
            "name": "BODETIME-Setup.exe",
            "state": "uploaded",
            "browser_download_url": "https://github.com/leonardo236/BODETIME/releases/download/v1.0.5/BODETIME-Setup.exe",
            "digest": "sha256:" + "a" * 64,
            "size": 1234,
        }],
    }
    monkeypatch.setattr(updater, "urlopen", lambda *_args, **_kwargs: FakeResponse(
        json.dumps(payload).encode(), updater.RELEASE_API
    ))
    result = get_latest_release("1.0.4")
    assert result == ReleaseInfo(
        "1.0.5", "v1.0.5", "https://github.com/leonardo236/BODETIME/releases/tag/v1.0.5",
        payload["assets"][0]["browser_download_url"], "a" * 64, 1234,
    )

    payload["assets"][0]["browser_download_url"] = "https://example.com/installer.exe"
    with pytest.raises(UpdateError, match="no coincide"):
        get_latest_release("1.0.4")


@pytest.mark.parametrize("bad_digest", [None, "sha1:" + "b" * 40, "sha256:abc"])
def test_release_metadata_rejects_missing_or_weak_digest(monkeypatch, bad_digest):
    payload = {
        "tag_name": "v1.0.5", "draft": False, "prerelease": False,
        "assets": [{
            "name": "BODETIME-Setup.exe", "state": "uploaded",
            "browser_download_url": "https://github.com/leonardo236/BODETIME/releases/download/v1.0.5/BODETIME-Setup.exe",
            "digest": bad_digest, "size": 1234,
        }],
    }
    monkeypatch.setattr(updater, "urlopen", lambda *_args, **_kwargs: FakeResponse(
        json.dumps(payload).encode(), updater.RELEASE_API
    ))
    with pytest.raises(UpdateError, match="SHA-256"):
        get_latest_release("1.0.4")


def test_download_verifies_hash_and_reports_progress(monkeypatch, tmp_path):
    content = b"BODETIME installer fixture"
    release = ReleaseInfo(
        "1.0.5", "v1.0.5", "https://github.com/leonardo236/BODETIME/releases/tag/v1.0.5",
        "https://github.com/leonardo236/BODETIME/releases/download/v1.0.5/BODETIME-Setup.exe",
        hashlib.sha256(content).hexdigest(), len(content),
    )
    monkeypatch.setattr(updater, "urlopen", lambda *_args, **_kwargs: FakeResponse(
        content, "https://release-assets.githubusercontent.com/asset", {"Content-Length": str(len(content))}
    ))
    progress = []
    result = download_update(release, progress.append, destination_dir=tmp_path)
    assert result.read_bytes() == content
    assert progress == [100]
    assert sorted(path.name for path in Path(tmp_path).iterdir()) == ["BODETIME-Setup-v1.0.5.exe"]


def test_download_never_keeps_a_tampered_installer(monkeypatch, tmp_path):
    release = ReleaseInfo(
        "1.0.5", "v1.0.5", "https://github.com/leonardo236/BODETIME/releases/tag/v1.0.5",
        "https://github.com/leonardo236/BODETIME/releases/download/v1.0.5/BODETIME-Setup.exe",
        "0" * 64, 4,
    )
    monkeypatch.setattr(updater, "urlopen", lambda *_args, **_kwargs: FakeResponse(
        b"bad!", "https://release-assets.githubusercontent.com/asset", {"Content-Length": "4"}
    ))
    with pytest.raises(UpdateError, match="integridad"):
        download_update(release, destination_dir=tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_download_can_be_cancelled_without_leaving_partial_file(monkeypatch, tmp_path):
    release = ReleaseInfo(
        "1.0.5", "v1.0.5", "https://github.com/leonardo236/BODETIME/releases/tag/v1.0.5",
        "https://github.com/leonardo236/BODETIME/releases/download/v1.0.5/BODETIME-Setup.exe",
        hashlib.sha256(b"x").hexdigest(), 1,
    )
    monkeypatch.setattr(updater, "urlopen", lambda *_args, **_kwargs: FakeResponse(
        b"x", "https://release-assets.githubusercontent.com/asset", {"Content-Length": "1"}
    ))
    cancelled = Event()
    cancelled.set()
    with pytest.raises(UpdateCancelled):
        download_update(release, cancel_event=cancelled, destination_dir=tmp_path)
    assert list(tmp_path.iterdir()) == []
