from __future__ import annotations

import html


_ICON_PATHS = {
    "activity": [
        '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>',
    ],
    "settings": [
        '<line x1="4" y1="21" x2="4" y2="14"></line>',
        '<line x1="4" y1="10" x2="4" y2="3"></line>',
        '<line x1="12" y1="21" x2="12" y2="12"></line>',
        '<line x1="12" y1="8" x2="12" y2="3"></line>',
        '<line x1="20" y1="21" x2="20" y2="16"></line>',
        '<line x1="20" y1="12" x2="20" y2="3"></line>',
        '<line x1="1" y1="14" x2="7" y2="14"></line>',
        '<line x1="9" y1="8" x2="15" y2="8"></line>',
        '<line x1="17" y1="16" x2="23" y2="16"></line>',
    ],
    "thermometer": [
        '<path d="M14 14.76V3.5a2.5 2.5 0 0 0-5 0v11.26a4 4 0 1 0 5 0z"></path>',
    ],
    "zap": [
        '<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>',
    ],
    "gauge": [
        '<path d="M12 14l4-4"></path>',
        '<path d="M3.34 19a10 10 0 1 1 17.32 0"></path>',
    ],
    "alert-circle": [
        '<circle cx="12" cy="12" r="10"></circle>',
        '<line x1="12" y1="8" x2="12" y2="12"></line>',
        '<line x1="12" y1="16" x2="12.01" y2="16"></line>',
    ],
    "alert-triangle": [
        '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>',
        '<line x1="12" y1="9" x2="12" y2="13"></line>',
        '<line x1="12" y1="17" x2="12.01" y2="17"></line>',
    ],
    "check-circle": [
        '<circle cx="12" cy="12" r="10"></circle>',
        '<polyline points="9 12 11.5 14.5 15.5 10.5"></polyline>',
    ],
    "shield-check": [
        '<path d="M12 2l7 3v6c0 5-3.2 9.1-7 11-3.8-1.9-7-6-7-11V5l7-3z"></path>',
        '<polyline points="8.8 12.3 11 14.5 15.5 10"></polyline>',
    ],
    "bar-chart": [
        '<line x1="12" y1="20" x2="12" y2="10"></line>',
        '<line x1="18" y1="20" x2="18" y2="4"></line>',
        '<line x1="6" y1="20" x2="6" y2="16"></line>',
    ],
    "clock": [
        '<circle cx="12" cy="12" r="10"></circle>',
        '<polyline points="12 6 12 12 16 14"></polyline>',
    ],
    "train": [
        '<rect x="4" y="3" width="16" height="14" rx="2"></rect>',
        '<line x1="8" y1="21" x2="16" y2="21"></line>',
        '<line x1="12" y1="17" x2="12" y2="21"></line>',
        '<circle cx="8.5" cy="13.5" r="1.5"></circle>',
        '<circle cx="15.5" cy="13.5" r="1.5"></circle>',
    ],
    "home": [
        '<path d="M3 10.5L12 3l9 7.5"></path>',
        '<path d="M5 9.5V20h14V9.5"></path>',
    ],
    "bell": [
        '<path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9"></path>',
        '<path d="M13.73 21a2 2 0 0 1-3.46 0"></path>',
    ],
    "wrench": [
        '<path d="M14.7 6.3a4 4 0 0 0-5.4 5.4L3 18l3 3 6.3-6.3a4 4 0 0 0 5.4-5.4l-2.4 2.4-2.6-.6-.6-2.6z"></path>',
    ],
    "trending-up": [
        '<polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline>',
        '<polyline points="17 6 23 6 23 12"></polyline>',
    ],
    "refresh-cw": [
        '<polyline points="23 4 23 10 17 10"></polyline>',
        '<polyline points="1 20 1 14 7 14"></polyline>',
        '<path d="M3.51 9a9 9 0 0 1 14.13-3.36L23 10"></path>',
        '<path d="M20.49 15a9 9 0 0 1-14.13 3.36L1 14"></path>',
    ],
    "droplet": [
        '<path d="M12 2.7C12 2.7 6 9.2 6 13.2a6 6 0 0 0 12 0c0-4-6-10.5-6-10.5z"></path>',
    ],
}


def icon_svg(name: str, size: int = 18, stroke: str = "currentColor", stroke_width: float = 2.0) -> str:
    safe_name = str(name or "").strip()
    paths = _ICON_PATHS.get(safe_name, _ICON_PATHS["bar-chart"])
    inner = "".join(paths)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{int(size)}" height="{int(size)}" '
        f'viewBox="0 0 24 24" fill="none" stroke="{html.escape(stroke)}" '
        f'stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round">{inner}</svg>'
    )


def _hex_to_rgba(hex_color: str, alpha: float) -> str:
    value = str(hex_color or "").strip().lstrip("#")
    if len(value) != 6:
        return f"rgba(35, 75, 141, {alpha})"
    r = int(value[0:2], 16)
    g = int(value[2:4], 16)
    b = int(value[4:6], 16)
    return f"rgba({r}, {g}, {b}, {alpha})"


def icon_chip(name: str, color: str = "#234B8D", size: int = 18, chip_size: int = 36) -> str:
    rgba = _hex_to_rgba(color, 0.16)
    svg = icon_svg(name=name, size=size, stroke=color, stroke_width=2)
    return (
        f'<span class="ds-icon-chip" style="--icon-bg:{rgba}; --icon-color:{color};'
        f'width:{int(chip_size)}px;height:{int(chip_size)}px;">{svg}</span>'
    )
