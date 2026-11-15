#!/usr/bin/env python3
"""Generates the Pinvyn v0.1 wiring plan from the layout file.

Outputs:
  layout/pinvyn-v0.1-wiring-left.svg, -right.svg  matrix seen from below
  docs/wiring.md                                  matrix tables and pin plan
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LAYOUT = ROOT / "layout" / "pinvyn-v0.1-layout.json"

MATRIX = {
    "left": {
        "rows": 5, "cols": 6,
        "grid": [
            ["`", "1", "2", "3", "4", "5"],
            ["Tab", "Q", "W", "E", "R", "T"],
            ["Shift", "A", "S", "D", "F", "G"],
            ["Ctrl", "Z", "X", "C", "V", "B"],
            ["Esc", "Win", "Fn", "Alt", "Space", "Caps"],
        ],
    },
    "right": {
        "rows": 6, "cols": 8,
        "grid": [
            ["LMB", "B", "RMB", None, "PrtSc", "Ins", "Home", "End"],
            ["6", "7", "8", "9", "0", "-", "=", "Bksp"],
            ["Y", "U", "I", "O", "P", "[", "]", "\\"],
            ["H", "J", "K", "L", ";", "'", "Enter", None],
            ["N", "M", ",", ".", "/", "Shift", "Up", "Del"],
            ["Space", None, None, "Fn", None, "Left", "Down", "Right"],
        ],
    },
}

PINS = {
    "left": {
        "rows": ["P0.31 (D21)", "P0.29 (D20)", "P0.02 (D19)", "P1.15 (D18)", "P1.13 (D15)"],
        "cols": ["P0.24 (D5)", "P1.00 (D6)", "P0.11 (D7)", "P1.04 (D8)", "P1.06 (D9)", "P0.09 (D10)"],
        "other": [
            ("Display MOSI", "P0.17 (D2)"), ("Display SCK", "P0.20 (D3)"), ("Display CS", "P0.06 (D1)"),
            ("Link TX, to right RX", "P0.08 (D0)"), ("Link RX, from right TX", "P0.22 (D4)"),
            ("Scroll V, A", "P1.11 (D14)"), ("Scroll V, B", "P0.10 (D16)"),
            ("Scroll H, A", "P1.01 (pad underneath)"), ("Scroll H, B", "P1.02 (pad underneath)"),
            ("Spare", "P1.07 (pad underneath)"),
        ],
    },
    "right": {
        "rows": ["P0.31 (D21)", "P0.29 (D20)", "P0.02 (D19)", "P1.15 (D18)", "P1.13 (D15)", "P1.11 (D14)"],
        "cols": ["P0.17 (D2)", "P0.20 (D3)", "P0.22 (D4)", "P0.24 (D5)", "P1.00 (D6)", "P0.11 (D7)",
                 "P1.04 (D8)", "P1.06 (D9)"],
        "other": [
            ("Link TX, to left RX", "P0.06 (D1)"), ("Link RX, from left TX", "P0.08 (D0)"),
            ("Sensor SCLK", "P0.10 (D16)"), ("Sensor SDIO", "P0.09 (D10)"),
            ("Sensor NCS", "P1.01 (pad underneath)"), ("Sensor MOTION", "P1.02 (pad underneath)"),
            ("Spare", "P1.07 (pad underneath)"),
        ],
    },
}

JUMPERS = {
    "left": {"rows": {"Esc", "Caps"}, "cols": {"Caps"}},
    "right": {"rows": {"LMB", "B", "RMB"}, "cols": {"LMB", "B", "RMB"}},
}

ROW_COLOURS = ["#A32D2D", "#BA7517", "#3B6D11", "#0F6E56", "#993556", "#712B13"]
COL_COLOUR = "#185FA5"
SHOW = {"Up": "↑", "Down": "↓", "Left": "←", "Right": "→"}


def assign(layout):
    for name, spec in MATRIX.items():
        keys = {k["label"]: k for k in layout["halves"][name]["keys"]}
        seen = set()
        for r, row in enumerate(spec["grid"]):
            for c, label in enumerate(row):
                if label is None:
                    continue
                assert label in keys and label not in seen, (name, label)
                seen.add(label)
                keys[label]["row"], keys[label]["col"] = r, c
        assert seen == set(keys), (name, set(keys) - seen)


def svg(name, half):
    s, pad = 56.0, 30.0
    width_u = half["width_u"]
    max_y = max(k["cy"] for k in half["keys"]) + 1.2
    w, h = width_u * s + 2 * pad, max_y * s + 2 * pad + 50

    def pos(k):
        return pad + (width_u - k["cx"]) * s, pad + 30 + k["cy"] * s

    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.0f} {h:.0f}" '
           f'font-family="Helvetica, Arial, sans-serif" font-size="12">',
           f'<title>Pinvyn v0.1 wiring, {name} half, seen from below</title>',
           f'<rect width="{w:.0f}" height="{h:.0f}" fill="#ffffff"/>',
           f'<text x="{pad:.0f}" y="{pad:.0f}" fill="#2C2C2A" font-size="14">{name.capitalize()} half, '
           f'seen from below (the side you solder on)</text>']
    for k in half["keys"]:
        x, y = pos(k)
        kw, kh = k["w"] * s - 6, s - 6
        rot = f' transform="rotate({-k["rot"]} {x:.1f} {y:.1f})"' if k["rot"] else ""
        out.append(f'<rect x="{x - kw / 2:.1f}" y="{y - kh / 2:.1f}" width="{kw:.1f}" height="{kh:.1f}" rx="6" '
                   f'fill="#F1EFE8" stroke="#888780" stroke-width="1"{rot}/>')
    def wires(members, order, jumpers, colour, dx, dy, dash):
        chain = sorted((k for k in members if k["label"] not in jumpers), key=order)
        d = " ".join(f'{pos(k)[0] + dx:.1f},{pos(k)[1] + dy:.1f}' for k in chain)
        out.append(f'<polyline points="{d}" fill="none" stroke="{colour}" stroke-width="2"{dash}/>')
        joined = list(chain)
        loose = [k for k in members if k["label"] in jumpers]
        while loose:
            a, b = min(((j, c) for j in loose for c in joined),
                       key=lambda p: (p[0]["cx"] - p[1]["cx"]) ** 2 + (p[0]["cy"] - p[1]["cy"]) ** 2)
            out.append(f'<line x1="{pos(a)[0] + dx:.1f}" y1="{pos(a)[1] + dy:.1f}" x2="{pos(b)[0] + dx:.1f}" '
                       f'y2="{pos(b)[1] + dy:.1f}" stroke="{colour}" stroke-width="2"{dash}/>')
            loose.remove(a)
            joined.append(a)

    for c in range(MATRIX[name]["cols"]):
        wires([k for k in half["keys"] if k["col"] == c], lambda k: k["cy"], JUMPERS[name]["cols"],
              COL_COLOUR, -14, 0, "")
    for r in range(MATRIX[name]["rows"]):
        wires([k for k in half["keys"] if k["row"] == r], lambda k: -k["cx"], JUMPERS[name]["rows"],
              ROW_COLOURS[r], 0, 14, ' stroke-dasharray="7 3"')
    for k in half["keys"]:
        x, y = pos(k)
        label = SHOW.get(k["label"], k["label"]).replace("&", "&amp;").replace("<", "&lt;")
        out.append(f'<text x="{x + 6:.1f}" y="{y - 8:.1f}" text-anchor="middle" fill="#2C2C2A">{label}</text>')
        out.append(f'<text x="{x + 6:.1f}" y="{y + 6:.1f}" text-anchor="middle" fill="#5F5E5A" '
                   f'font-size="10">R{k["row"]} C{k["col"]}</text>')
    ly = h - pad - 4
    out.append(f'<line x1="{pad:.0f}" y1="{ly:.0f}" x2="{pad + 40:.0f}" y2="{ly:.0f}" stroke="{COL_COLOUR}" stroke-width="2"/>')
    out.append(f'<text x="{pad + 48:.0f}" y="{ly + 4:.0f}" fill="#444441">Column wire (solid)</text>')
    out.append(f'<line x1="{pad + 200:.0f}" y1="{ly:.0f}" x2="{pad + 240:.0f}" y2="{ly:.0f}" stroke="{ROW_COLOURS[0]}" '
               f'stroke-width="2" stroke-dasharray="7 3"/>')
    out.append(f'<text x="{pad + 248:.0f}" y="{ly + 4:.0f}" fill="#444441">Row wire (dashed), via the diodes</text>')
    out.append("</svg>")
    return "\n".join(out) + "\n"


def table(name):
    spec = MATRIX[name]
    head = "| | " + " | ".join(f"C{c}" for c in range(spec["cols"])) + " |"
    sep = "|---|" + "---|" * spec["cols"]
    rows = [head, sep]
    for r, row in enumerate(spec["grid"]):
        cells = [("`` ` ``" if x == "`" else SHOW.get(x, x).replace("\\", "\\\\")) if x else "" for x in row]
        rows.append(f"| **R{r}** | " + " | ".join(cells) + " |")
    return "\n".join(rows)


def pin_table(name):
    p = PINS[name]
    rows = ["| Line | Controller pin |", "|---|---|"]
    rows += [f"| Row R{i} | {pin} |" for i, pin in enumerate(p["rows"])]
    rows += [f"| Column C{i} | {pin} |" for i, pin in enumerate(p["cols"])]
    rows += [f"| {a} | {b} |" for a, b in p["other"]]
    return "\n".join(rows)


DOC = """# Pinvyn v0.1 wiring plan

Generated by `layout/generate_wiring.py`. Edit the script, not this file.

Everything here is a plan that has not been built yet. Items tagged **VERIFY** must be checked against the actual boards and current ZMK documentation before soldering.

## How the matrix works

Each key sits at one row and one column. The controller finds a pressed key by which row and column are connected. One diode per key stops false presses when several keys are held.

- Diode direction: **the striped end of every diode goes to the row wire.** The other end goes to one switch pin.
- The other switch pin goes to the column wire.
- In ZMK this is `diode-direction = "col2row"`.
- Rows and columns are electrical groups. Most follow the physical rows and columns; a few keys are placed where a free slot was. Those need a short jumper wire, and the wires are insulated, so they may cross.

## Left half: 5 rows × 6 columns, 30 keys

![Left half wiring](../layout/pinvyn-v0.1-wiring-left.svg)

{left_table}

Jumpers: Esc joins row R4 with a wire down the outer edge. Caps joins row R4 and column C5.

{left_pins}

## Right half: 6 rows × 8 columns, 43 keys

![Right half wiring](../layout/pinvyn-v0.1-wiring-right.svg)

{right_table}

Jumpers: the two mouse buttons and the second B join row R0, which otherwise holds the four top keys. Their column wires are the three nearest columns.

{right_pins}

## Pin names

Pins are given as the nRF52840 port name with the Pro Micro position in brackets. A nice!nano v2-type board has 18 pins on its edges and three pads underneath (P1.01, P1.02, P1.07). **VERIFY** the labels printed on the boards you bought; clones sometimes differ.

P0.09 and P0.10 double as NFC antenna pins on this chip. **VERIFY** that the firmware build uses them as normal pins.

## Cable between the halves (TRRS)

| Contact | Line | Left pin | Right pin |
|---|---|---|---|
| Tip | Power | see below | see below |
| Ring 1 | Left TX to right RX | P0.08 (D0) | P0.08 (D0) |
| Ring 2 | Right TX to left RX | P0.22 (D4) | P0.06 (D1) |
| Sleeve | Ground | GND | GND |

TX on one half always goes to RX on the other.

Power to the right half is **not decided. VERIFY** before wiring. The two candidates are the left board's 3.3 V pin to the right board's 3.3 V pin, or battery voltage to the right board's battery input.

Switch the keyboard off before plugging or unplugging this cable. The plug touches several contacts as it slides in.

## Other parts

- **Display (left):** three signal wires as in the table, plus 3.3 V and ground. These pins follow the usual nice!view wiring. **VERIFY** against the display's documentation.
- **Scrollers (left):** each encoder has two signal pins, A and B, and a common pin that goes to ground.
- **Trackball sensor (right):** four signal wires as in the table, plus power and ground. **VERIFY** the supply voltage of the sensor board you bought; some need 1.8 V and carry their own regulator.
- **Battery (left):** to the board's battery pads, through the slide switch on the positive wire.

## Order of work

1. Fit all switches into the plate.
2. Solder a diode to one pin of every switch, striped end pointing away from the switch.
3. Join the striped ends along each row. Add the jumpers.
4. Run a column wire along the free pin of each switch in a column. Add the jumpers.
5. Before connecting the controller, test with a multimeter: every row against every column should show no connection until a key is pressed.
6. Wire rows and columns to the controller, then the other parts.
7. Flash, and test every key before closing the case.
"""


def main():
    layout = json.loads(LAYOUT.read_text())
    assign(layout)
    LAYOUT.write_text(json.dumps(layout, indent=2, ensure_ascii=False) + "\n")
    for name, half in layout["halves"].items():
        (ROOT / "layout" / f"pinvyn-v0.1-wiring-{name}.svg").write_text(svg(name, half))
    (ROOT / "docs" / "wiring.md").write_text(DOC.format(
        left_table=table("left"), left_pins=pin_table("left"),
        right_table=table("right"), right_pins=pin_table("right")))
    for name in MATRIX:
        used = len(PINS[name]["rows"]) + len(PINS[name]["cols"]) + len(PINS[name]["other"])
        pins = [p for p in PINS[name]["rows"] + PINS[name]["cols"]] + [b for _, b in PINS[name]["other"]]
        assert len(set(pins)) == len(pins), name
        print(name, "pins listed:", used, "unique:", len(set(pins)))


if __name__ == "__main__":
    main()
