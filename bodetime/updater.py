"""Consulta y descarga segura del instalador publicado en GitHub Releases."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from threading import Event
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from .version import APP_VERSION


RELEASE_API = "https://api.github.com/repos/leonardo236/BODETIME/releases/latest"
REPOSITORY_RELEASES = "https://github.com/leonardo236/BODETIME/releases"
MAX_INSTALLER_SIZE = 300 * 1024 * 1024


class UpdateError(RuntimeError):
    """Error de consulta, integridad o descarga de una actualización."""


class UpdateCancelled(UpdateError):
    """La persona canceló la descarga."""


@dataclass(frozen=True)
class ReleaseInfo:
    version: str
    tag: str
    notes_url: str
    installer_url: str
    installer_sha256: str
    installer_size: int


def _version_tuple(value: str) -> tuple[int, int, int]:
    match = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)", value.strip())
    if not match:
        raise UpdateError("La versión publicada no tiene un formato válido.")
    return tuple(map(int, match.groups()))


def is_newer_version(candidate: str, current: str = APP_VERSION) -> bool:
    return _version_tuple(candidate) > _version_tuple(current)


def get_latest_release(current_version: str = APP_VERSION) -> ReleaseInfo | None:
    """Consulta GitHub; devuelve solo versiones nuevas, publicadas y verificables."""
    request = Request(
        RELEASE_API,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "BODETIME-Updater",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urlopen(request, timeout=6) as response:
            if urlsplit(response.geturl()).hostname != "api.github.com":
                raise UpdateError("La respuesta de actualización no provino de GitHub API.")
            release = json.loads(response.read(2_000_000).decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise UpdateError("No se pudo consultar GitHub. Comprueba tu conexión e inténtalo de nuevo.") from exc

    tag = release.get("tag_name", "")
    version = tag[1:] if isinstance(tag, str) and tag.startswith("v") else tag
    if not isinstance(version, str) or not is_newer_version(version, current_version):
        return None
    if release.get("draft") or release.get("prerelease"):
        return None

    expected_url = f"https://github.com/leonardo236/BODETIME/releases/download/v{version}/BODETIME-Setup.exe"
    for asset in release.get("assets", []):
        if asset.get("name") != "BODETIME-Setup.exe" or asset.get("state") != "uploaded":
            continue
        digest = asset.get("digest", "")
        size = asset.get("size")
        url = asset.get("browser_download_url", "")
        if not isinstance(digest, str) or not re.fullmatch(r"sha256:[0-9a-fA-F]{64}", digest):
            raise UpdateError("GitHub no publicó una suma SHA-256 para el instalador.")
        if not isinstance(size, int) or not 0 < size <= MAX_INSTALLER_SIZE:
            raise UpdateError("El tamaño del instalador publicado no es válido.")
        if url != expected_url:
            raise UpdateError("El enlace del instalador no coincide con el repositorio oficial de BODETIME.")
        return ReleaseInfo(
            version=version,
            tag=tag,
            notes_url=f"{REPOSITORY_RELEASES}/tag/{tag}",
            installer_url=url,
            installer_sha256=digest.split(":", 1)[1].lower(),
            installer_size=size,
        )
    raise UpdateError("La publicación nueva todavía no contiene un instalador verificable.")


def download_update(
    release: ReleaseInfo,
    progress_callback=None,
    cancel_event: Event | None = None,
    destination_dir: str | Path | None = None,
) -> Path:
    """Descarga el setup, comprueba tamaño y SHA-256 y luego lo deja listo."""
    request = Request(release.installer_url, headers={"User-Agent": "BODETIME-Updater"})
    allowed_hosts = {"github.com", "release-assets.githubusercontent.com", "objects.githubusercontent.com"}
    folder = Path(destination_dir) if destination_dir else Path(
        os.getenv("LOCALAPPDATA", tempfile.gettempdir())
    ) / "BODETIME" / "updates"
    folder.mkdir(parents=True, exist_ok=True)
    destination = folder / f"BODETIME-Setup-v{release.version}.exe"
    temporary = folder / f".{destination.name}.part"
    digest = hashlib.sha256()
    received = 0
    try:
        with urlopen(request, timeout=5) as response, temporary.open("wb") as output:
            final_host = urlsplit(response.geturl()).hostname
            if final_host not in allowed_hosts:
                raise UpdateError("La descarga se redirigió a un servidor no autorizado.")
            content_length = response.headers.get("Content-Length")
            if content_length and int(content_length) != release.installer_size:
                raise UpdateError("El tamaño anunciado del instalador no coincide con el publicado.")
            while True:
                if cancel_event and cancel_event.is_set():
                    raise UpdateCancelled("La descarga fue cancelada.")
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                received += len(chunk)
                if received > release.installer_size or received > MAX_INSTALLER_SIZE:
                    raise UpdateError("La descarga excedió el tamaño publicado.")
                output.write(chunk)
                digest.update(chunk)
                if progress_callback:
                    progress_callback(min(100, int(received * 100 / release.installer_size)))
        if received != release.installer_size:
            raise UpdateError("La descarga quedó incompleta; inténtalo de nuevo.")
        if digest.hexdigest() != release.installer_sha256:
            raise UpdateError("La verificación de integridad falló; no se ejecutó el instalador.")
        os.replace(temporary, destination)
        return destination
    except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
        if isinstance(exc, UpdateError):
            raise
        raise UpdateError("No se pudo descargar la actualización. Inténtalo de nuevo.") from exc
    finally:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
