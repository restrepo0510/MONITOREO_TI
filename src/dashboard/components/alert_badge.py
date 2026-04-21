import streamlit as st


_LEVEL_STYLES = {
    "ALTO": {
        "bg": "linear-gradient(135deg,#A61E2E 0%,#D32F2F 100%)",
        "text": "#F4F4F9",
        "border": "rgba(166,30,46,0.24)",
    },
    "MEDIO": {
        "bg": "linear-gradient(135deg,#FFE600 0%,#FFD000 100%)",
        "text": "#0F1E3C",
        "border": "rgba(255,208,0,0.24)",
    },
    "BAJO": {
        "bg": "linear-gradient(135deg,#234B8D 0%,#173A73 100%)",
        "text": "#F4F4F9",
        "border": "rgba(35,75,141,0.22)",
    },
}


def render_alert_badge(
    level: str,
    label: str = "Nivel actual",
    caption: str = "",
) -> None:
    normalized = str(level or "BAJO").upper()
    style = _LEVEL_STYLES.get(normalized, _LEVEL_STYLES["BAJO"])
    st.html(f"""
        <div style="
            background:{style['bg']};
            color:{style['text']};
            border:1px solid {style['border']};
            border-radius:18px;
            padding:0.95rem 1rem;
            box-shadow:0 18px 32px rgba(15,30,60,0.10);
            font-family:inherit;
        ">
            <div style="font-size:0.78rem;letter-spacing:0.11em;text-transform:uppercase;
                        opacity:0.85;margin-bottom:0.3rem;font-weight:700;">
                {label}
            </div>
            <div style="font-size:1.48rem;line-height:1.05;font-weight:800;margin-bottom:0.22rem;">
                {normalized}
            </div>
            <div style="font-size:0.88rem;line-height:1.4;opacity:0.94;">
                {caption}
            </div>
        </div>
    """)
