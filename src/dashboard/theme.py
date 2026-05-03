PALETTE = {
    "yellow": "#F6C50E",
    "black": "#000000",
    "light_blue": "#B8DBD9",
    "ghost_white": "#F9F8F8",
    "steel_azure": "#082A70",
    "alert_red": "#D32F2F",
}


RISK_THEME = {
    "ALTO": {
        "bg": PALETTE["alert_red"],
        "text": PALETTE["ghost_white"],
        "line": "#FFD6D6",
    },
    "MEDIO": {
        "bg": PALETTE["yellow"],
        "text": PALETTE["black"],
        "line": "#6B6200",
    },
    "BAJO": {
        "bg": PALETTE["steel_azure"],
        "text": PALETTE["ghost_white"],
        "line": PALETTE["light_blue"],
    },
    "MISSING": {
        "bg": "#3A3D46",
        "text": PALETTE["ghost_white"],
        "line": "#90949D",
    },
}

RISK_THRESHOLDS = {
    "MEDIO": 0.4,
    "ALTO": 0.7,
}


def risk_palette(level):
    return RISK_THEME.get(level, RISK_THEME["BAJO"])
