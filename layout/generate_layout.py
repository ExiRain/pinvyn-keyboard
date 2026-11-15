#!/usr/bin/env python3
"""Generates the Pinvyn v0.1 layout files from one definition.

Outputs, next to this script:
  pinvyn-v0.1-layout.json  key and part positions per half
  pinvyn-v0.1-layout.svg   overview drawing

Units are key units (1u = 19.05 mm). Each half has its own origin at its
top-left corner, x to the right, y down. Positions are centres. Rotation is
in degrees, clockwise when seen from above.
"""
import json
import math
from pathlib import Path

U_MM = 19.05
HERE = Path(__file__).resolve().parent

LEFT_STAGGER = [0.375, 0.375, 0.125, 0.0, 0.125, 0.25]
RIGHT_STAGGER = [0.25, 0.125, 0.0, 0.125, 0.375, 0.375, 0.375, 0.375]
RIGHT_KEYS_X = 2.9

FN_LAYER = {
    "1": "F1", "2": "F2", "3": "F3", "4": "F4", "5": "F5", "6": "F6",
    "7": "F7", "8": "F8", "9": "F9", "0": "F10", "-": "F11", "=": "F12",
}


def key(label, cx, cy, w=1.0, rot=0.0, note=None):
    k = {"label": label, "cx": round(cx, 4), "cy": round(cy, 4), "w": w, "h": 1.0, "rot": rot}
    if label in FN_LAYER:
        k["fn"] = FN_LAYER[label]
    if note:
        k["note"] = note
    return k


def grid(label, x, y, w=1.0):
    return key(label, x + w / 2, y + 0.5, w)


def part(kind, label, cx, cy, w, h, rot=0.0, note=None):
    p = {"kind": kind, "label": label, "cx": cx, "cy": cy, "w": w, "h": h, "rot": rot}
    if note:
        p["note"] = note
    return p


def left_half():
    keys = [grid("Esc", 0, LEFT_STAGGER[0])]
    rows = [
        ["`", "1", "2", "3", "4", "5"],
        ["Tab", "Q", "W", "E", "R", "T"],
        ["Shift", "A", "S", "D", "F", "G"],
        ["Ctrl", "Z", "X", "C", "V", "B"],
    ]
    for r, row in enumerate(rows):
        for c, label in enumerate(row):
            keys.append(grid(label, c, r + 1 + LEFT_STAGGER[c]))
    keys += [
        key("Win", 0.92, 5.95),
        key("Fn", 1.95, 5.95, note="hold layer key"),
        key("Alt", 3.05, 5.95, rot=4),
        key("Space", 4.7, 6.05, w=2.0, rot=8, note="2u, stabilizer"),
        key("Caps", 6.75, 3.4, note="set apart from the G column on purpose"),
    ]
    parts = [
        part("display", "Display", 7.92, 1.95, 0.735, 1.89,
             note="nice!view type, 14 x 36 mm, battery status; left controller sits under it"),
        part("scroll_h", "Scroll H", 7.1, 4.75, 1.75, 0.65, rot=20,
             note="left/right scroll, mouse-wheel encoder with printed wheel"),
        part("scroll_v", "Scroll V", 6.75, 6.2, 0.7, 1.6, rot=20,
             note="up/down scroll, mouse-wheel encoder with printed wheel"),
    ]
    return {"width_u": 8.4, "keys": keys, "parts": parts}


def right_half():
    kx = RIGHT_KEYS_X
    keys = []
    for c, label in zip([4, 5, 6, 7], ["PrtSc", "Ins", "Home", "End"]):
        keys.append(grid(label, kx + c, RIGHT_STAGGER[c]))
    rows = [
        ["6", "7", "8", "9", "0", "-", "=", "Bksp"],
        ["Y", "U", "I", "O", "P", "[", "]", "\\"],
        ["H", "J", "K", "L", ";", "'", None, None],
        ["N", "M", ",", ".", "/", "Shift", "Up", "Del"],
    ]
    for r, row in enumerate(rows):
        for c, label in enumerate(row):
            if label:
                keys.append(grid(label, kx + c, r + 1 + RIGHT_STAGGER[c]))
    enter = grid("Enter", kx + 6, 3 + RIGHT_STAGGER[6], w=2.0)
    enter["note"] = "2u, stabilizer"
    keys.append(enter)
    for c, label in zip([5, 6, 7], ["Left", "Down", "Right"]):
        keys.append(grid(label, kx + c, 5 + RIGHT_STAGGER[c]))
    keys += [
        key("Space", kx + 1.25, 5.95, w=2.0, rot=-8, note="2u, stabilizer"),
        key("Fn", kx + 2.95, 5.75, note="second hold layer key"),
        key("RMB", kx - 1.7, 3.9, rot=-12, note="right mouse button"),
        grid("LMB", kx - 1, 3.25),
        grid("B", kx - 1, 4.25),
    ]
    keys[-2]["note"] = "left mouse button, index finger"
    keys[-1]["note"] = "second B"
    parts = [
        part("trackball", "Ball", kx - 1.05, 6.25, 1.785, 1.785,
             note="34 mm ball, thumb operated, PMW3610 sensor underneath"),
        part("controller", "MCU", 0.75, 1.875, 1.2, 1.75,
             note="right controller, hidden inside the case, no display on this half"),
    ]
    return {"width_u": 10.9, "keys": keys, "parts": parts}


def corners(item):
    r = math.radians(item["rot"])
    hw, hh = item["w"] / 2, item["h"] / 2
    return [
        (item["cx"] + dx * math.cos(r) - dy * math.sin(r),
         item["cy"] + dx * math.sin(r) + dy * math.cos(r))
        for dx, dy in [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]
    ]


def bounds(half):
    pts = [p for item in half["keys"] + half["parts"] for p in corners(item)]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


ARROWS = {"Up": "↑", "Down": "↓", "Left": "←", "Right": "→", "Scroll H": "H scroll", "Scroll V": "V"}


def svg(layout):
    s = 48.0
    gap = 0.6
    pad = 30.0
    left, right = layout["halves"]["left"], layout["halves"]["right"]
    offsets = {"left": 0.0, "right": left["width_u"] + gap}
    total_w = left["width_u"] + gap + right["width_u"]
    max_y = max(bounds(left)[3], bounds(right)[3])
    width = total_w * s + 2 * pad
    height = max_y * s + 2 * pad + 60
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.0f} {height:.0f}" '
        f'font-family="Helvetica, Arial, sans-serif" font-size="13">',
        f'<title>Pinvyn v0.1 layout</title>',
        f'<rect width="{width:.0f}" height="{height:.0f}" fill="#ffffff"/>',
    ]
    for name, half in layout["halves"].items():
        ox = pad + offsets[name] * s
        oy = pad + 24
        out.append(f'<text x="{ox + 2:.1f}" y="{pad + 6:.1f}" fill="#444441">{name.capitalize()} half</text>')
        for k in half["keys"]:
            w, h = k["w"] * s - 4, k["h"] * s - 4
            cx, cy = ox + k["cx"] * s, oy + k["cy"] * s
            wide = k["w"] > 1
            fill, stroke = ("#E1F5EE", "#0F6E56") if wide else ("#F1EFE8", "#5F5E5A")
            rot = f' transform="rotate({k["rot"]} {cx:.1f} {cy:.1f})"' if k["rot"] else ""
            out.append(f'<rect x="{cx - w / 2:.1f}" y="{cy - h / 2:.1f}" width="{w:.1f}" height="{h:.1f}" '
                       f'rx="6" fill="{fill}" stroke="{stroke}" stroke-width="1"{rot}/>')
            label = ARROWS.get(k["label"], k["label"]).replace("&", "&amp;").replace("<", "&lt;")
            out.append(f'<text x="{cx:.1f}" y="{cy:.1f}" text-anchor="middle" dominant-baseline="central" '
                       f'fill="#2C2C2A">{label}</text>')
        for p in half["parts"]:
            cx, cy = ox + p["cx"] * s, oy + p["cy"] * s
            if p["kind"] == "trackball":
                out.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{p["w"] * s / 2:.1f}" fill="#EEEDFE" '
                           f'stroke="#534AB7" stroke-width="1" stroke-dasharray="5 4"/>')
            else:
                w, h = p["w"] * s, p["h"] * s
                rot = f' transform="rotate({p["rot"]} {cx:.1f} {cy:.1f})"' if p["rot"] else ""
                out.append(f'<rect x="{cx - w / 2:.1f}" y="{cy - h / 2:.1f}" width="{w:.1f}" height="{h:.1f}" '
                           f'rx="6" fill="#EEEDFE" stroke="#534AB7" stroke-width="1" stroke-dasharray="5 4"{rot}/>')
            label = ARROWS.get(p["label"], p["label"])
            if p["kind"] == "display":
                label = "LCD"
            out.append(f'<text x="{cx:.1f}" y="{cy:.1f}" text-anchor="middle" dominant-baseline="central" '
                       f'fill="#3C3489">{label}</text>')
    ly = height - pad - 8
    legend = [("#F1EFE8", "#5F5E5A", "", "1u key"), ("#E1F5EE", "#0F6E56", "", "2u key, needs stabilizer"),
              ("#EEEDFE", "#534AB7", ' stroke-dasharray="5 4"', "Other part")]
    lx = pad
    for fill, stroke, dash, text in legend:
        out.append(f'<rect x="{lx:.1f}" y="{ly - 9:.1f}" width="18" height="18" rx="4" fill="{fill}" '
                   f'stroke="{stroke}" stroke-width="1"{dash}/>')
        out.append(f'<text x="{lx + 26:.1f}" y="{ly:.1f}" dominant-baseline="central" fill="#444441">{text}</text>')
        lx += 60 + len(text) * 7.5
    out.append("</svg>")
    return "\n".join(out) + "\n"


def main():
    layout = {
        "name": "Pinvyn",
        "version": "v0.1",
        "unit_mm": U_MM,
        "conventions": "per-half origin at top-left, x right, y down, positions are centres in key units, "
                       "rot in degrees clockwise seen from above",
        "halves": {"left": left_half(), "right": right_half()},
    }
    for half in layout["halves"].values():
        x0, y0, x1, y1 = bounds(half)
        half["bounds_mm"] = {"width": round((x1 - x0) * U_MM, 1), "height": round((y1 - y0) * U_MM, 1)}
        half["key_count"] = len(half["keys"])
    (HERE / "pinvyn-v0.1-layout.json").write_text(json.dumps(layout, indent=2, ensure_ascii=False) + "\n")
    (HERE / "pinvyn-v0.1-layout.svg").write_text(svg(layout))
    for name, half in layout["halves"].items():
        print(name, half["key_count"], "keys", half["bounds_mm"])


if __name__ == "__main__":
    main()
