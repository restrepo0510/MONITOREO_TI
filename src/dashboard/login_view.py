from __future__ import annotations

import base64
import html
import re
import time
from pathlib import Path
from typing import Any
from urllib.parse import quote

import streamlit as st

from src.dashboard.auth_service import (
    AuthError,
    get_user,
    logout,
    refresh_session,
    sign_in_authorized_operator,
)


AUTH_SESSION_KEY = "supabase_auth_session"
AUTH_USER_KEY = "supabase_auth_user"

ASSET_DIR = Path(__file__).resolve().parent / "assets" / "images"
VIDEO_DIR = Path(__file__).resolve().parent / "assets" / "videos"
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def require_login() -> bool:
    """Renderiza el login cuando no hay sesion activa."""
    _refresh_existing_session()
    if is_authenticated():
        return True

    render_login_screen()
    return False


def is_authenticated() -> bool:
    session = st.session_state.get(AUTH_SESSION_KEY)
    user = st.session_state.get(AUTH_USER_KEY)
    return bool(session and user and session.get("access_token"))


def current_user() -> dict[str, Any]:
    user = st.session_state.get(AUTH_USER_KEY) or {}
    if "user" in user and isinstance(user["user"], dict):
        return user["user"]
    return user


def render_auth_sidebar() -> None:
    user = current_user()
    email = html.escape(str(user.get("email", "usuario@metro.local")))
    metadata = user.get("user_metadata") or {}
    full_name = html.escape(str(metadata.get("full_name") or "Operador Metro"))

    st.markdown(
        f"""
        <div class="auth-side-card">
            <div class="auth-side-avatar">M</div>
            <div>
                <div class="auth-side-name">{full_name}</div>
                <div class="auth-side-email">{email}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Cerrar sesion", use_container_width=True, key="auth_logout"):
        _perform_logout()
        st.rerun()


def render_login_screen() -> None:
    _inject_login_css()
    train_uri = _asset_data_uri("train.png")
    logo_uri = _asset_data_uri("logo.png")
    video_uri = _video_data_uri("metro_oporto.mp4")

    left, right = st.columns([1.18, 0.82], gap="large")

    with left:
        st.markdown(_left_hero_markup(train_uri, video_uri), unsafe_allow_html=True)

    with right:
        st.markdown(_login_header_markup(logo_uri), unsafe_allow_html=True)
        _render_sign_in_form()


def _render_sign_in_form() -> None:
    with st.form("supabase_sign_in", clear_on_submit=False):
        email = st.text_input("Correo electronico", key="login_email")
        password = st.text_input("Contrasena", type="password", key="login_password")
        submitted = st.form_submit_button(
            "Entrar al centro de control", use_container_width=True
        )

    if submitted:
        if not _valid_email(email):
            _show_error("Escribe un correo valido.")
            return
        if not password:
            _show_error("Escribe tu contrasena.")
            return

        try:
            session = sign_in_authorized_operator(email, password)
            _store_session(session)
            st.success("Sesion iniciada. Preparando el dashboard...")
            time.sleep(0.45)
            st.rerun()
        except AuthError as exc:
            _show_error(str(exc))


def _store_session(session: dict[str, Any]) -> None:
    expires_in = int(session.get("expires_in") or 3600)
    session["expires_at"] = int(time.time()) + expires_in
    st.session_state[AUTH_SESSION_KEY] = session

    user = session.get("user")
    if user:
        st.session_state[AUTH_USER_KEY] = user
        return

    access_token = session.get("access_token")
    if access_token:
        st.session_state[AUTH_USER_KEY] = get_user(access_token)


def _refresh_existing_session() -> None:
    session = st.session_state.get(AUTH_SESSION_KEY) or {}
    refresh_token = session.get("refresh_token")
    access_token = session.get("access_token")
    expires_at = int(session.get("expires_at") or 0)
    now = int(time.time())

    if not refresh_token or not access_token:
        if access_token and expires_at and expires_at <= now:
            _clear_auth_state()
        return
    if expires_at and expires_at - now > 90:
        return

    try:
        refreshed = refresh_session(refresh_token)
        _store_session(refreshed)
    except AuthError:
        _clear_auth_state()


def _perform_logout() -> None:
    session = st.session_state.get(AUTH_SESSION_KEY) or {}
    access_token = session.get("access_token")
    if access_token and session.get("provider") != "metro_operator_allowlist":
        try:
            logout(access_token)
        except AuthError:
            pass
    _clear_auth_state()


def _clear_auth_state() -> None:
    st.session_state.pop(AUTH_SESSION_KEY, None)
    st.session_state.pop(AUTH_USER_KEY, None)


def _valid_email(email: str) -> bool:
    return bool(EMAIL_RE.match(email.strip()))


def _show_error(message: str) -> None:
    st.error(message)


@st.cache_data(show_spinner=False)
def _asset_data_uri(filename: str) -> str:
    path = ASSET_DIR / filename
    mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{data}"


@st.cache_data(show_spinner=False)
def _video_data_uri(filename: str) -> str:
    path = VIDEO_DIR / filename
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:video/mp4;base64,{data}"


def _metro_cursor_data_uri() -> str:
    svg = """
    <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 48 48">
      <defs>
        <linearGradient id="g" x1="8" y1="4" x2="40" y2="44" gradientUnits="userSpaceOnUse">
          <stop stop-color="#FFE600"/>
          <stop offset="0.42" stop-color="#F6C50E"/>
          <stop offset="1" stop-color="#082A70"/>
        </linearGradient>
      </defs>
      <path d="M24 4C15.2 4 9 10.1 9 19v9.6C9 36.3 15.5 43 24 43s15-6.7 15-14.4V19C39 10.1 32.8 4 24 4Z" fill="url(#g)" stroke="#050505" stroke-width="2"/>
      <path d="M14 18c.7-5.1 4.4-8.2 10-8.2s9.3 3.1 10 8.2H14Z" fill="#F9F8F8" stroke="#050505" stroke-width="1.5"/>
      <path d="M14 21h20v8H14z" fill="#102A44" stroke="#050505" stroke-width="1.4"/>
      <path d="M17.2 29.5h13.6" stroke="#B8DBD9" stroke-width="1.7" stroke-linecap="round"/>
      <circle cx="17.2" cy="34.8" r="2.6" fill="#F9F8F8" stroke="#050505" stroke-width="1"/>
      <circle cx="30.8" cy="34.8" r="2.6" fill="#F9F8F8" stroke="#050505" stroke-width="1"/>
      <path d="M20.4 16.6c0-1.3.9-2.2 2.1-2.2s2.1.9 2.1 2.2v1.7c0 .9.7 1.6 1.6 1.6s1.6-.7 1.6-1.6v-3.7" fill="none" stroke="#082A70" stroke-width="2.5" stroke-linecap="round"/>
      <path d="M7 7l9 4-7 4Z" fill="#050505"/>
    </svg>
    """
    return f"data:image/svg+xml,{quote(svg.strip())}"


def _inject_login_css() -> None:
    cursor_uri = _metro_cursor_data_uri()
    st.markdown(
        f"""
        <style>
        :root {{
            --login-ink: #050505;
            --login-paper: #F9F8F8;
            --login-blue: #082A70;
            --login-yellow: #FFE600;
            --login-gold: #F6C50E;
            --login-mint: #B8DBD9;
            --login-red: #FF4F5F;
            --login-green: #2DD4BF;
        }}

        * {{
            cursor: url("{cursor_uri}") 8 8, auto !important;
        }}

        [data-testid="stSidebar"],
        [data-testid="stSidebarNav"],
        [data-testid="collapsedControl"] {{
            display: none !important;
        }}

        [data-testid="stHeader"] {{
            display: none !important;
            height: 0 !important;
            background: transparent !important;
        }}

        [data-testid="stToolbar"],
        .stAppToolbar {{
            display: none !important;
        }}

        [data-testid="stAppViewContainer"] {{
            background:
                linear-gradient(90deg, rgba(255, 230, 0, 0.12) 1px, transparent 1px),
                linear-gradient(180deg, rgba(8, 42, 112, 0.08) 1px, transparent 1px),
                #F9F8F8 !important;
            background-size: 34px 34px;
        }}

        [data-testid="stMainBlockContainer"],
        .main .block-container {{
            max-width: 1480px !important;
            padding: 1.35rem 1.55rem 2rem !important;
        }}

        .porto-hero {{
            position: relative;
            overflow: hidden;
            min-height: 740px;
            border: 3px solid var(--login-ink);
            border-radius: 30px;
            background: #FFFFFF;
            box-shadow: 14px 14px 0 #050505;
        }}

        .porto-hero-top {{
            position: relative;
            z-index: 3;
            display: flex;
            justify-content: space-between;
            gap: 1rem;
            padding: 1.2rem 1.25rem 0;
        }}

        .porto-pill {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-height: 38px;
            padding: 0.45rem 0.9rem;
            border: 2px solid var(--login-ink);
            border-radius: 999px;
            background: var(--login-yellow);
            color: var(--login-ink);
            font-size: 0.82rem;
            font-weight: 900;
            text-transform: uppercase;
            letter-spacing: 0;
            box-shadow: 4px 4px 0 #050505;
        }}

        .porto-pill.blue {{
            background: var(--login-blue);
            color: #FFFFFF;
        }}

        .porto-title-wrap {{
            position: relative;
            z-index: 3;
            padding: 1.2rem 1.35rem 0;
            max-width: 850px;
        }}

        .porto-kicker {{
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            color: var(--login-blue);
            font-weight: 950;
            font-size: 0.95rem;
            text-transform: uppercase;
        }}

        .porto-title {{
            color: var(--login-ink);
            font-size: clamp(3.05rem, 6vw, 6.7rem);
            line-height: 0.88;
            font-weight: 1000;
            margin: 0.5rem 0 0.6rem;
            letter-spacing: 0;
        }}

        .porto-copy {{
            max-width: 680px;
            color: #222222;
            font-size: 1.08rem;
            line-height: 1.45;
            font-weight: 650;
            margin: 0;
        }}

        .porto-video {{
            position: relative;
            height: 350px;
            margin: 1.15rem 1.35rem 0;
            border: 3px solid var(--login-ink);
            border-radius: 26px;
            overflow: hidden;
            background: #050505;
            box-shadow: 8px 8px 0 #050505;
            isolation: isolate;
        }}

        .porto-video::before {{
            content: "";
            position: absolute;
            inset: 0;
            background:
                linear-gradient(90deg, rgba(255, 230, 0, 0.16) 1px, transparent 1px),
                linear-gradient(180deg, rgba(255, 255, 255, 0.10) 1px, transparent 1px),
                radial-gradient(circle at 50% 42%, rgba(255, 230, 0, 0.2), transparent 46%),
                #050505;
            background-size: 30px 30px, 30px 30px, cover, cover;
            opacity: 1;
            z-index: 1;
        }}

        .porto-video-frame {{
            position: absolute;
            inset: 0;
            z-index: 3;
            width: 100%;
            height: 100%;
            border: 0;
            background: #050505;
            object-fit: cover;
            pointer-events: none;
        }}

        .video-interaction-lock {{
            position: absolute;
            inset: 0;
            z-index: 5;
            background: transparent;
        }}

        .photo-strip {{
            position: relative;
            z-index: 4;
            overflow: hidden;
            margin: 1.05rem 1.35rem 0;
            padding: 0.2rem 0 0.8rem;
            min-height: 152px;
        }}

        .photo-track {{
            display: flex;
            width: max-content;
            gap: 0.85rem;
            animation: photo-loop 18s linear infinite;
        }}

        .photo-card {{
            width: 184px;
            height: 132px;
            flex: 0 0 auto;
            border: 2px solid #050505;
            border-radius: 20px;
            overflow: hidden;
            background: var(--card-bg, #FFFFFF);
            box-shadow: 5px 5px 0 #050505;
            position: relative;
        }}

        .photo-card img {{
            position: absolute;
            width: 190px;
            left: -24px;
            bottom: 18px;
            filter: drop-shadow(0 10px 7px rgba(0, 0, 0, 0.26));
        }}

        .photo-card span {{
            position: absolute;
            left: 10px;
            bottom: 9px;
            background: #FFFFFF;
            border: 1.8px solid #050505;
            border-radius: 999px;
            padding: 0.24rem 0.48rem;
            font-size: 0.7rem;
            font-weight: 900;
            color: #050505;
        }}

        .typing-card {{
            position: absolute;
            left: 50%;
            top: 50%;
            transform: translate(-50%, -50%);
            z-index: 6;
            width: min(360px, calc(100% - 2rem));
            border: 3px solid #050505;
            border-radius: 22px;
            background: #FFFFFF;
            padding: 1rem;
            box-shadow: 8px 8px 0 #050505;
        }}

        .typing-top {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin-bottom: 0.65rem;
        }}

        .typing-avatar {{
            width: 44px;
            height: 44px;
            border: 2px solid #050505;
            border-radius: 50%;
            background:
                radial-gradient(circle at 50% 36%, #050505 0 5px, transparent 6px),
                radial-gradient(circle at 50% 78%, #050505 0 14px, transparent 15px),
                #FFE600;
        }}

        .typing-name {{
            color: #050505;
            font-size: 0.87rem;
            font-weight: 950;
            line-height: 1.1;
        }}

        .typing-role {{
            color: #52616F;
            font-size: 0.72rem;
            font-weight: 800;
            margin-top: 0.12rem;
        }}

        .typing-text {{
            color: #050505;
            font-size: 1.07rem;
            line-height: 1.18;
            font-weight: 950;
            min-height: 45px;
        }}

        .typing-line {{
            display: block;
            overflow: hidden;
            white-space: nowrap;
            width: 0;
            max-width: max-content;
        }}

        .typing-line.first {{
            animation: type-first 6s steps(29, end) infinite;
        }}

        .typing-line.second {{
            animation: type-second 6s steps(13, end) infinite;
        }}

        .typing-line.second::after {{
            content: "";
            display: inline-block;
            width: 8px;
            height: 1rem;
            margin-left: 4px;
            background: #082A70;
            animation: caret-blink 0.74s steps(2, jump-none) infinite;
            vertical-align: -2px;
        }}

        .login-brand {{
            border: 3px solid #050505;
            border-radius: 30px 30px 0 0;
            background: #FFFFFF;
            padding: 1.2rem 1.2rem 0.8rem;
            box-shadow: 10px 10px 0 #050505;
        }}

        .login-brand-row {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
        }}

        .login-logo {{
            width: 78px;
            height: 78px;
            object-fit: contain;
            border: 2px solid #050505;
            border-radius: 50%;
            background: #FFFFFF;
        }}

        .login-live {{
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            background: #2DD4BF;
            color: #050505;
            border: 2px solid #050505;
            border-radius: 999px;
            padding: 0.42rem 0.72rem;
            font-size: 0.78rem;
            font-weight: 950;
            box-shadow: 4px 4px 0 #050505;
        }}

        .login-live::before {{
            content: "";
            width: 9px;
            height: 9px;
            border-radius: 999px;
            background: #050505;
            animation: live-dot 1.2s ease-in-out infinite;
        }}

        .login-title {{
            margin: 0.95rem 0 0.2rem;
            color: #050505;
            font-size: clamp(2rem, 3.6vw, 3.2rem);
            line-height: 0.94;
            font-weight: 1000;
            letter-spacing: 0;
        }}

        .login-subtitle {{
            color: #26313D;
            margin: 0;
            font-size: 1rem;
            line-height: 1.42;
            font-weight: 700;
        }}

        div[data-testid="stForm"] {{
            border: 3px solid #050505;
            border-top: 0;
            border-radius: 0 0 30px 30px;
            background: #FFFFFF;
            padding: 0.75rem 1.05rem 1.15rem;
            box-shadow: 10px 10px 0 #050505;
        }}

        div[data-testid="stTextInput"] label p {{
            color: #050505;
            font-weight: 950;
            font-size: 0.88rem;
        }}

        div[data-baseweb="input"] > div,
        div[data-baseweb="input"] {{
            background: #FFFFFF !important;
            border-color: #050505 !important;
            border-radius: 16px !important;
            box-shadow: 4px 4px 0 #050505 !important;
        }}

        div[data-baseweb="input"] input {{
            min-height: 48px;
            color: #050505 !important;
            font-weight: 780;
        }}

        .stForm button,
        .stButton button {{
            min-height: 52px;
            border: 2px solid #050505 !important;
            border-radius: 18px !important;
            background: #082A70 !important;
            color: #FFFFFF !important;
            font-weight: 1000 !important;
            box-shadow: 5px 5px 0 #050505 !important;
            transition: transform 150ms ease, box-shadow 150ms ease, background 150ms ease;
        }}

        .stForm button:hover,
        .stButton button:hover {{
            background: #FFE600 !important;
            color: #050505 !important;
            transform: translate(2px, 2px);
            box-shadow: 3px 3px 0 #050505 !important;
        }}

        div[data-testid="stAlert"] {{
            border: 2px solid #050505;
            border-radius: 16px;
            box-shadow: 4px 4px 0 #050505;
            font-weight: 800;
        }}

        .auth-side-card {{
            display: flex;
            align-items: center;
            gap: 0.7rem;
            padding: 0.8rem;
            margin-bottom: 0.75rem;
            border: 1px solid rgba(255, 255, 255, 0.28);
            border-radius: 18px;
            background: rgba(255, 255, 255, 0.10);
        }}

        .auth-side-avatar {{
            width: 42px;
            height: 42px;
            flex: 0 0 auto;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
            background: #F6C50E;
            color: #082A70 !important;
            font-weight: 1000;
        }}

        .auth-side-name {{
            color: #FFFFFF !important;
            font-weight: 900;
            line-height: 1.15;
            font-size: 0.92rem;
        }}

        .auth-side-email {{
            color: rgba(255, 255, 255, 0.74) !important;
            font-weight: 650;
            line-height: 1.2;
            font-size: 0.76rem;
            word-break: break-word;
        }}

        @keyframes photo-loop {{
            from {{ transform: translateX(0); }}
            to {{ transform: translateX(-50%); }}
        }}

        @keyframes type-first {{
            0%, 8% {{ width: 0; }}
            48%, 100% {{ width: 29ch; }}
        }}

        @keyframes type-second {{
            0%, 48% {{ width: 0; }}
            72%, 100% {{ width: 13ch; }}
        }}

        @keyframes caret-blink {{
            0%, 48% {{ opacity: 1; }}
            49%, 100% {{ opacity: 0; }}
        }}

        @keyframes live-dot {{
            0%, 100% {{ transform: scale(1); opacity: 1; }}
            50% {{ transform: scale(0.55); opacity: 0.65; }}
        }}

        @media (max-width: 1050px) {{
            .porto-hero {{
                min-height: 610px;
            }}

            .porto-video {{
                height: 300px;
            }}
        }}

        @media (max-width: 760px) {{
            [data-testid="stMainBlockContainer"],
            .main .block-container {{
                padding: 0.9rem 0.85rem 1.6rem !important;
            }}

            div[data-testid="stHorizontalBlock"] {{
                flex-direction: column !important;
                gap: 1.2rem !important;
            }}

            div[data-testid="column"] {{
                width: 100% !important;
                flex: 1 1 100% !important;
                min-width: 100% !important;
            }}

            .porto-hero {{
                min-height: auto;
                border-radius: 24px;
                box-shadow: 7px 7px 0 #050505;
            }}

            .porto-hero-top {{
                flex-wrap: wrap;
            }}

            .porto-video {{
                height: 255px;
                margin: 0.9rem;
                border-radius: 20px;
            }}

            .porto-title-wrap,
            .photo-strip {{
                margin-left: 0;
                margin-right: 0;
                padding-left: 0.95rem;
                padding-right: 0.95rem;
            }}

            .photo-card {{
                width: 156px;
                height: 116px;
            }}

            .login-brand,
            div[data-testid="stForm"] {{
                box-shadow: 7px 7px 0 #050505;
            }}

            div[data-testid="stForm"] {{
                padding: 0.7rem 0.45rem 1.05rem;
            }}

            .typing-card {{
                width: min(318px, calc(100% - 0.8rem));
                padding: 0.8rem;
            }}

            .typing-line.first {{
                animation-name: type-first-mobile;
            }}

            .typing-text {{
                font-size: 0.95rem;
            }}
        }}

        @keyframes type-first-mobile {{
            0%, 8% {{ width: 0; }}
            48%, 100% {{ width: 29ch; }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _left_hero_markup(train_uri: str, video_uri: str) -> str:
    cards = [
        ("Trindade", "#FFE600"),
        ("Bolhao", "#B8DBD9"),
        ("Aliados", "#FFFFFF"),
        ("Campanha", "#F6C50E"),
        ("Casa da Musica", "#DDE7FF"),
        ("Sao Bento", "#D9F99D"),
    ]
    photo_cards = "".join(
        f'<div class="photo-card" style="--card-bg:{color}">'
        f'<img src="{train_uri}" alt="Metro do Porto en {html.escape(name)}">'
        f"<span>{html.escape(name)}</span></div>"
        for name, color in cards + cards
    )

    return f"""
    <section class="porto-hero" aria-label="Metro do Porto login hero">
        <div class="porto-hero-top">
            <span class="porto-pill">Metro do Porto</span>
            <span class="porto-pill blue">Acceso operativo</span>
        </div>
        <div class="porto-title-wrap">
            <div class="porto-kicker">Control predictivo en vivo</div>
            <h1 class="porto-title">Dashboard Metro Do Porto.</h1>
            <p class="porto-copy">
                Sistema que protege trenes, sensores y toma decisiones criticas del Metro do Porto.
            </p>
        </div>
        <div class="porto-video" aria-label="Video del Metro do Porto en movimiento">
            <video
                class="porto-video-frame"
                src="{video_uri}"
                autoplay
                muted
                loop
                playsinline
                preload="auto"
            ></video>
            <div class="video-interaction-lock" aria-hidden="true"></div>
        </div>
        <div class="photo-strip" aria-label="Carrusel Metro do Porto">
            <div class="photo-track">{photo_cards}</div>
            <aside class="typing-card" aria-label="Mensaje operativo">
                <div class="typing-top">
                    <div class="typing-avatar" aria-hidden="true"></div>
                    <div>
                        <div class="typing-name">Operadora digitando</div>
                        <div class="typing-role">Centro de control Metro do Porto</div>
                    </div>
                </div>
                <div class="typing-text" aria-label="El mejor transporte del mundo entra seguro.">
                    <span class="typing-line first">Bienvenido al Dashboard del</span>
                    <span class="typing-line second">Metro Do Porto.</span>
                </div>
            </aside>
        </div>
    </section>
    """


def _login_header_markup(logo_uri: str) -> str:
    return f"""
    <section class="login-brand" aria-label="Acceso Metro do Porto">
        <div class="login-brand-row">
            <img class="login-logo" src="{logo_uri}" alt="Logo Metro do Porto">
            <span class="login-live">Acceso restringido</span>
        </div>
        <h2 class="login-title">Acceso Metro do Porto</h2>
        <p class="login-subtitle">
            Ingreso exclusivo para administración y gerencia del centro de control.
        </p>
    </section>
    """
