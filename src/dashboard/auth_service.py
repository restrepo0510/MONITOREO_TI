from __future__ import annotations

import json
import os
import secrets
import time
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


DEFAULT_SUPABASE_REST_URL = "https://fgixilnsdokwwnhopfcf.supabase.co/rest/v1/"
DEFAULT_SUPABASE_KEY = "sb_publishable_b6cTgMNvJ-UHHCEvImKxWA_JCVahu6n"

ALLOWED_OPERATOR_EMAILS = {
    "admin1@metrooporto.com": "Administrador 1",
    "admin2@metrooporto.com": "Administrador 2",
    "gerencia@metrooporto.com": "Gerencia Metro do Porto",
}
OPERATOR_PASSWORD = os.getenv("METRO_OPERATOR_PASSWORD", "metrooporto")


@dataclass
class AuthError(Exception):
    message: str
    status_code: int | None = None
    details: dict[str, Any] | None = None

    def __str__(self) -> str:
        return self.message


def _project_base_url() -> str:
    raw_url = (
        os.getenv("SUPABASE_URL")
        or os.getenv("SUPABASE_REST_URL")
        or DEFAULT_SUPABASE_REST_URL
    ).strip()
    parsed = urlparse(raw_url)
    if not parsed.scheme or not parsed.netloc:
        raise AuthError("La URL de Supabase no es valida.")

    return f"{parsed.scheme}://{parsed.netloc}"


def _publishable_key() -> str:
    key = (
        os.getenv("SUPABASE_PUBLISHABLE_KEY")
        or os.getenv("SUPABASE_ANON_KEY")
        or DEFAULT_SUPABASE_KEY
    ).strip()
    if not key:
        raise AuthError("Falta la llave publica de Supabase.")
    return key


def _headers(access_token: str | None = None) -> dict[str, str]:
    headers = {
        "apikey": _publishable_key(),
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    return headers


def _request(
    method: str,
    path: str,
    payload: dict[str, Any] | None = None,
    access_token: str | None = None,
) -> dict[str, Any]:
    base_url = _project_base_url()
    body = json.dumps(payload or {}).encode("utf-8") if payload is not None else None
    request = Request(
        f"{base_url}{path}",
        data=body,
        headers=_headers(access_token=access_token),
        method=method.upper(),
    )

    try:
        with urlopen(request, timeout=18) as response:
            response_body = response.read().decode("utf-8")
            if not response_body:
                return {}
            return json.loads(response_body)
    except HTTPError as exc:
        raw_error = exc.read().decode("utf-8", errors="replace")
        details = _safe_json(raw_error)
        raise AuthError(
            _humanize_error(details) or "No se pudo completar la autenticacion.",
            status_code=exc.code,
            details=details,
        ) from exc
    except URLError as exc:
        raise AuthError(
            "No hay conexion con Supabase. Revisa internet o la URL del proyecto.",
            details={"reason": str(exc.reason)},
        ) from exc
    except json.JSONDecodeError as exc:
        raise AuthError("Supabase respondio con un formato inesperado.") from exc


def _safe_json(raw_error: str) -> dict[str, Any]:
    try:
        parsed = json.loads(raw_error)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass
    return {"message": raw_error}


def _humanize_error(details: dict[str, Any]) -> str:
    raw = str(
        details.get("msg")
        or details.get("message")
        or details.get("error_description")
        or details.get("error")
        or ""
    )
    normalized = raw.lower()

    if "invalid login credentials" in normalized:
        return "Correo o contrasena incorrectos."
    if "email not confirmed" in normalized:
        return "Tu correo aun no esta confirmado. Revisa el enlace de Supabase."
    if "user already registered" in normalized or "already registered" in normalized:
        return "Ya existe una cuenta con ese correo."
    if "password" in normalized and ("weak" in normalized or "short" in normalized):
        return "La contrasena debe ser mas fuerte."
    if "rate limit" in normalized or "too many" in normalized:
        return "Demasiados intentos. Espera un momento y vuelve a probar."

    return raw


def sign_in_with_password(email: str, password: str) -> dict[str, Any]:
    return _request(
        "POST",
        "/auth/v1/token?grant_type=password",
        {"email": email.strip(), "password": password},
    )


def sign_in_authorized_operator(email: str, password: str) -> dict[str, Any]:
    normalized_email = email.strip().lower()
    full_name = ALLOWED_OPERATOR_EMAILS.get(normalized_email)

    if not full_name or password != OPERATOR_PASSWORD:
        raise AuthError("Correo o contrasena no autorizados para este dashboard.")

    issued_at = int(time.time())
    expires_in = 12 * 60 * 60
    access_token = f"metro-local-{secrets.token_urlsafe(32)}"

    return {
        "access_token": access_token,
        "refresh_token": "",
        "token_type": "bearer",
        "expires_in": expires_in,
        "expires_at": issued_at + expires_in,
        "provider": "metro_operator_allowlist",
        "user": {
            "id": f"metro-{normalized_email.split('@', 1)[0]}",
            "email": normalized_email,
            "aud": "authenticated",
            "role": "authenticated",
            "created_at": "2026-05-03T00:00:00Z",
            "user_metadata": {
                "full_name": full_name,
                "access_scope": "dashboard_operativo",
            },
        },
    }


def refresh_session(refresh_token: str) -> dict[str, Any]:
    return _request(
        "POST",
        "/auth/v1/token?grant_type=refresh_token",
        {"refresh_token": refresh_token},
    )


def get_user(access_token: str) -> dict[str, Any]:
    return _request("GET", "/auth/v1/user", access_token=access_token)


def logout(access_token: str) -> None:
    _request("POST", "/auth/v1/logout", {}, access_token=access_token)
