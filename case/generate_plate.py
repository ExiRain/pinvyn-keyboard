#!/usr/bin/env python3
"""Generates printable switch plates for Pinvyn v0.1 from the layout file.

Outputs, next to this script:
  pinvyn-v0.1-plate-left.stl, pinvyn-v0.1-plate-right.stl  plate with a skirt and feet
  pinvyn-v0.1-ball-adapter.stl                             holds the trackball module under the right plate
  pinvyn-v0.1-coupon.stl                                   small fit-test piece

Needs: pip install shapely trimesh mapbox-earcut manifold3d

The top of the plate is at z = 0, switches go in from above. All sizes in mm.
Scroller openings are placeholders until the real parts are measured. The
stabilizer cutout is a common Cherry plate-mount size and must be checked
against the stabilizers bought.

Trackball: the ball sits in pointabella's "mount top static bearing 34mm"
on top of its "mount mid (pmw3610-siderakb)" (github.com/badjeff/pointabella,
CERN-OHL-P v2). Those two parts are printed from pointabella's STLs. The
adapter here screws under the plate and carries them, turned 180 degrees so
an open side faces the second B key. Their screw positions below are taken
from those STLs.
"""
import argparse
import json
import math
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
    "scroll_scale": 0.8,   # placeholder opening as a share of the scroller footprint
    "ball_opening": 44.0,  # hole in the plate; the holder's pillars reach 20.6 mm from the centre
    "ball_ring": 9.0,      # plate width kept around the ball hole
    "ball_top": 18.0,      # top of the 34 mm ball above the plate top, keycaps end about 12-14
    "ball_in_mount": 17.5, # ball centre above the bottom of pointabella's top mount, with ceramic balls in
    "mount_rot": 180.0,    # turn of the pointabella holder, degrees
    "mid_height": 5.0,     # pointabella mount mid, from its bosses to the top mount
    "floor": 2.5,          # adapter floor under the mount mid
    "flange": 3.0,         # adapter ring under the plate
    "flange_in": 22.5,
    "flange_out": 28.5,
    "leg_angles": (100, 210, 330),
    "leg_in": 19.0,
    "leg_out": 27.0,
    "leg_w": 7.0,
    "screw_r": 25.0,       # M2 screws from the top, through the plate into the flange and legs
    "screw_clear": 2.3,
    "screw_pilot": 1.7,
    "mid_bosses": ((-8.75, 12.75), (8.75, 12.75), (-8.75, -12.75), (8.75, -12.75)),
    "wire_slot": (12.0, 18.0),
    "switch_body": 16.0,   # keep-out under the plate around every switch
    "foot_r": 4.0,
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


def ball_centre(half, u):
    for p in half["parts"]:
        if p["kind"] == "trackball":
            return p["cx"] * u, -p["cy"] * u
    return None


def screw_points(centre):
    cx, cy = centre
    return [(cx + P["screw_r"] * math.cos(math.radians(a)), cy + P["screw_r"] * math.sin(math.radians(a)))
            for a in P["leg_angles"]]


def part_shapes(p, u):
    if p["kind"] == "trackball":
        centre = Point(p["cx"] * u, -p["cy"] * u)
        r = P["ball_opening"] / 2
        cuts = [centre.buffer(r, 64)]
        cuts += [Point(s).buffer(P["screw_clear"] / 2, 24) for s in screw_points((centre.x, centre.y))]
        return centre.buffer(r + P["ball_ring"], 64), cuts
    w, h = p["w"] * u, p["h"] * u
    area = place(box(-w / 2, -h / 2, w / 2, h / 2), p, u)
    if p["kind"].startswith("scroll"):
        s = P["scroll_scale"]
        return area, [place(box(-w * s / 2, -h * s / 2, w * s / 2, h * s / 2), p, u)]
    return area, []


def adapter_depth():
    mount_bottom = P["ball_top"] - 17.0 - P["ball_in_mount"]
    return -(mount_bottom - P["mid_height"] - P["floor"])


def prism(shape, z0, z1):
    meshes = [trimesh.creation.extrude_polygon(g, z1 - z0) for g in getattr(shape, "geoms", [shape])]
    m = trimesh.util.concatenate(meshes)
    m.apply_translation((0, 0, z0))
    return m


def union(meshes):
    try:
        return trimesh.boolean.union(meshes, engine="manifold")
    except Exception:
        return trimesh.util.concatenate(meshes)


def feet(outline, centre):
    if not P.get("feet_h"):
        return []
    ring = outline.buffer(-P["skirt_wall"] / 2)
    xs, ys = ring.exterior.xy
    pts = list(zip(xs, ys))
    picks = [min(pts, key=lambda q: q[0] + q[1]), min(pts, key=lambda q: -q[0] + q[1]),
             min(pts, key=lambda q: q[0] - q[1]), min(pts, key=lambda q: -q[0] - q[1])]
    out = []
    for q in picks:
        if centre and math.dist(q, centre) < P["ball_opening"]:
            continue
        if any(math.dist(q, o) < 20 for o in out):
            continue
        out.append(q)
    z0 = -P["skirt_depth"] - P["feet_h"]
    return [prism(Point(q).buffer(P["foot_r"], 32).intersection(outline), z0, -P["skirt_depth"] + 0.2) for q in out]


def solid(outline, cuts, extra=()):
    plate = trimesh.creation.extrude_polygon(outline.difference(unary_union(cuts)), P["plate"])
    plate.apply_translation((0, 0, -P["plate"]))
    ring = outline.difference(outline.buffer(-P["skirt_wall"]))
    skirt = trimesh.creation.extrude_polygon(ring, P["skirt_depth"] - P["plate"] + 0.2)
    skirt.apply_translation((0, 0, -P["skirt_depth"]))
    return union([plate, skirt, *extra])


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
    return outline, cuts, solid(outline, cuts, feet(outline, ball_centre(half, u)))


def build_adapter(half, u):
    cx, cy = ball_centre(half, u)
    s = P["switch_body"] / 2
    keep_out = unary_union([place(box(-s, -s, s, s), k, u) for k in half["keys"]]).buffer(1.0)
    pilots = unary_union([Point(q).buffer(P["screw_pilot"] / 2, 24) for q in screw_points((cx, cy))])
    top = -P["plate"]
    bottom = -adapter_depth()
    floor_top = bottom + P["floor"]

    flange = Point(cx, cy).buffer(P["flange_out"], 64).difference(Point(cx, cy).buffer(P["flange_in"], 64))
    legs = []
    for a in P["leg_angles"]:
        leg = box(P["leg_in"], -P["leg_w"] / 2, P["leg_out"], P["leg_w"] / 2)
        legs.append(affinity.translate(affinity.rotate(leg, a, origin=(0, 0)), cx, cy))
    legs = unary_union(legs)
    flange = flange.difference(keep_out.difference(legs.buffer(0.01)))

    base = Point(cx, cy).buffer(P["leg_out"], 64)
    holes = [affinity.translate(affinity.rotate(Point(bx, by), P["mount_rot"], origin=(0, 0)), cx, cy).buffer(P["screw_pilot"] / 2, 24)
             for bx, by in P["mid_bosses"]]
    w, h = P["wire_slot"]
    slot = affinity.translate(box(-w / 2, -h / 2, w / 2, h / 2), cx, cy)
    floor = base.difference(unary_union([*holes, slot]))

    parts = [
        prism(flange.difference(pilots), top - P["flange"], top),
        prism(legs.difference(pilots), floor_top - 0.1, top - P["flange"] + 0.1),
        prism(floor, bottom, floor_top),
    ]
    return union(parts)


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
    ap.add_argument("--ball-top", type=float, help="ball top above the plate top, default 18")
    args = ap.parse_args()
    if args.hole:
        P["hole"] = args.hole
    if args.ball_top:
        P["ball_top"] = args.ball_top
    P["feet_h"] = adapter_depth() - P["skirt_depth"]
    layout = json.loads(LAYOUT.read_text())
    u = layout["unit_mm"]
    jobs = {f"plate-{n}": build_half(h, u) for n, h in layout["halves"].items()}
    jobs["coupon"] = build_coupon(u)
    for name, (outline, cuts, mesh) in jobs.items():
        mesh.export(HERE / f"pinvyn-v0.1-{name}.stl")
        x0, y0, x1, y1 = outline.bounds
        print(f"{name}: {x1 - x0:.1f} x {y1 - y0:.1f} mm, {len(cuts)} cutouts, watertight={mesh.is_watertight}")
    adapter = build_adapter(layout["halves"]["right"], u)
    adapter.export(HERE / "pinvyn-v0.1-ball-adapter.stl")
    print(f"ball-adapter: {adapter.extents[2]:.1f} mm tall, feet {P['feet_h']:.1f} mm, watertight={adapter.is_watertight}")
    return jobs


if __name__ == "__main__":
    main()
