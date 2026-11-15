#!/usr/bin/env python3
"""Generates printable switch plates for Pinvyn v0.1 from the layout file.

Outputs, next to this script:
  pinvyn-v0.1-plate-left.stl, pinvyn-v0.1-plate-right.stl  plate with a skirt
  pinvyn-v0.1-coupon.stl                                   small fit-test piece

Needs: pip install shapely trimesh mapbox-earcut manifold3d

The top of the plate is at z = 0, switches go in from above. All sizes in mm.
Trackball and scroller openings are placeholders until the real parts are
measured. The stabilizer cutout is a common Cherry plate-mount size and must
be checked against the stabilizers bought.
"""
import argparse
import json
from pathlib import Path

import trimesh
from shapely import affinity
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
LAYOUT = HERE.parent / "layout" / "pinvyn-v0.1-layout.json"

P = {
    "hole": 14.0,          # switch cutout, square
    "plate": 1.5,          # plate thickness where switches clip in
    "margin": 4.0,         # plate edge beyond the outermost key cells
    "fill": 12.0,          # notches in the outline narrower than twice this get filled
    "skirt_wall": 2.5,
    "skirt_depth": 10.0,   # from plate top to skirt bottom; switch pins reach about 8.3
    "stab_offset": 11.9,   # 2u stabilizer: cutout centres left and right of the switch
    "stab_w": 6.75,
    "stab_up": 5.53,       # cutout extent above the switch centre
    "stab_down": 6.77,     # and below it
    "ball_opening": 42.0,  # placeholder opening for the trackball cup
    "scroll_scale": 0.8,   # placeholder opening as a share of the scroller footprint
}


def place(shape, item, u):
    shape = affinity.rotate(shape, -item["rot"], origin=(0, 0))
    return affinity.translate(shape, item["cx"] * u, -item["cy"] * u)


def key_shapes(k, u):
    cell = place(box(-k["w"] * u / 2, -u / 2, k["w"] * u / 2, u / 2), k, u)
    h = P["hole"] / 2
    cuts = [box(-h, -h, h, h)]
    if k["w"] >= 2:
        for side in (-1, 1):
            x = side * P["stab_offset"]
            cuts.append(box(x - P["stab_w"] / 2, -P["stab_down"], x + P["stab_w"] / 2, P["stab_up"]))
    return cell, [place(c, k, u) for c in cuts]


def part_shapes(p, u):
    if p["kind"] == "trackball":
        centre = Point(p["cx"] * u, -p["cy"] * u)
        r = P["ball_opening"] / 2
        return centre.buffer(r + 5, 64), [centre.buffer(r, 64)]
    w, h = p["w"] * u, p["h"] * u
    area = place(box(-w / 2, -h / 2, w / 2, h / 2), p, u)
    if p["kind"].startswith("scroll"):
        s = P["scroll_scale"]
        return area, [place(box(-w * s / 2, -h * s / 2, w * s / 2, h * s / 2), p, u)]
    return area, []


def solid(outline, cuts):
    plate = trimesh.creation.extrude_polygon(outline.difference(unary_union(cuts)), P["plate"])
    plate.apply_translation((0, 0, -P["plate"]))
    ring = outline.difference(outline.buffer(-P["skirt_wall"]))
    skirt = trimesh.creation.extrude_polygon(ring, P["skirt_depth"] - P["plate"] + 0.2)
    skirt.apply_translation((0, 0, -P["skirt_depth"]))
    try:
        return trimesh.boolean.union([plate, skirt], engine="manifold")
    except Exception:
        return trimesh.util.concatenate([plate, skirt])


def outline_of(areas):
    m = P["margin"]
    shape = unary_union(areas).buffer(m + P["fill"], join_style=1).buffer(-P["fill"], join_style=1)
    if shape.geom_type != "Polygon":
        shape = max(shape.geoms, key=lambda g: g.area)
    return Polygon(shape.exterior)


def build_half(half, u):
    areas, cuts = [], []
    for k in half["keys"]:
        a, c = key_shapes(k, u)
        areas.append(a)
        cuts += c
    for p in half["parts"]:
        a, c = part_shapes(p, u)
        areas.append(a)
        cuts += c
    outline = outline_of(areas)
    return outline, cuts, solid(outline, cuts)


def build_coupon(u):
    keys = [{"cx": 0.5, "cy": 0.5, "w": 1, "rot": 0}, {"cx": 1.5, "cy": 0.5, "w": 1, "rot": 0},
            {"cx": 1.0, "cy": 1.5, "w": 2, "rot": 0}]
    areas, cuts = [], []
    for k in keys:
        a, c = key_shapes(k, u)
        areas.append(a)
        cuts += c
    outline = outline_of(areas)
    return outline, cuts, solid(outline, cuts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hole", type=float, help="switch cutout size, e.g. 14.1 if 14.0 prints tight")
    args = ap.parse_args()
    if args.hole:
        P["hole"] = args.hole
    layout = json.loads(LAYOUT.read_text())
    u = layout["unit_mm"]
    jobs = {f"plate-{n}": build_half(h, u) for n, h in layout["halves"].items()}
    jobs["coupon"] = build_coupon(u)
    for name, (outline, cuts, mesh) in jobs.items():
        mesh.export(HERE / f"pinvyn-v0.1-{name}.stl")
        x0, y0, x1, y1 = outline.bounds
        print(f"{name}: {x1 - x0:.1f} x {y1 - y0:.1f} mm, {len(cuts)} cutouts, watertight={mesh.is_watertight}")
    return jobs


if __name__ == "__main__":
    main()
