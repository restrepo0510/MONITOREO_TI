import streamlit as st


_TONE_STYLES = {
    "blue":   {"accent": "#234B8D", "bg": "#FFFFFF",  "border": "rgba(35,75,141,0.12)"},
    "yellow": {"accent": "#8D7300", "bg": "#FFFCE0",  "border": "rgba(213,183,0,0.22)"},
    "red":    {"accent": "#C0392B", "bg": "#FFF1F1",  "border": "rgba(192,57,43,0.18)"},
    "dark":   {"accent": "#0F1E3C", "bg": "#F4F4F9",  "border": "rgba(15,30,60,0.12)"},
}


def render_kpi_card(
    label: str,
    value: str,
    caption: str = "",
    delta: str = "",
    tone: str = "blue",
) -> None:
    style = _TONE_STYLES.get(tone, _TONE_STYLES["blue"])
    delta_html = (
        f'<div style="font-size:0.84rem;font-weight:700;color:{style["accent"]};margin-bottom:0.28rem;">{delta}</div>'
        if delta else ""
    )
    st.html(f"""
        <div style="
            background:{style['bg']};
            border-radius:18px;
            padding:1rem;
            border:1px solid {style['border']};
            box-shadow:0 18px 34px rgba(15,30,60,0.08);
            min-height:152px;
            font-family:inherit;
        ">
            <div style="font-size:0.78rem;text-transform:uppercase;letter-spacing:0.10em;
                        opacity:0.72;font-weight:700;margin-bottom:0.6rem;color:{style['accent']};">
                {label}
            </div>
            <div style="font-size:1.65rem;line-height:1.04;font-weight:800;
                        color:{style['accent']};margin-bottom:0.4rem;">
                {value}
            </div>
            {delta_html}
            <div style="font-size:0.86rem;line-height:1.42;color:#4A5672;">
                {caption}
            </div>
        </div>
    """)
