#!/usr/bin/env python3
"""Procedurally build the Hall of Supreme Harmony (Taihedian) from regulation
dimensions and render a still. Route-2 build for the Forbidden City project.
Run: blender -b --factory-startup -noaudio --python build_taihedian.py
Env overrides: TAIHE_OUT (png path), TAIHE_CAM 'x,y,z', TAIHE_TGT 'x,y,z',
TAIHE_LENS (mm), TAIHE_BLEND (blend path or '' to skip saving).
Dimensions (verified, metres): facade 63.96 wide (11 bays), depth 37,
hall height 26.92 above terrace, 3-tier marble terrace 8.13, total 35.05,
double-eaved hip roof, ridge chiwen 3.4. Origin = hall centre, ground z=0,
+Y = north (rear), -Y = south (front / plaza).
"""
import bpy, math, os
from mathutils import Vector

BASE = '/home/hatch/workspace/imagine_media/forbidden_city/'
OUT = os.environ.get('TAIHE_OUT', BASE + 'still/taihedian-procedural-still.png')
BLEND = os.environ.get('TAIHE_BLEND', BASE + 'blender/taihedian_scene.blend')

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# ---------- materials ----------
def make_mat(name, rgba, rough=0.9):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Base Color'].default_value = rgba
    bsdf.inputs['Roughness'].default_value = rough
    return m

MARBLE = make_mat('marble', (0.90, 0.87, 0.81, 1.0))
MARBLE2 = make_mat('marble_trim', (0.83, 0.79, 0.72, 1.0))
TIER_MATS = [make_mat('tier1', (0.78, 0.75, 0.68, 1.0)),
             make_mat('tier2', (0.85, 0.82, 0.75, 1.0)),
             make_mat('tier3', (0.92, 0.89, 0.83, 1.0))]
RED = make_mat('palace_red', (0.46, 0.07, 0.05, 1.0))
DARKRED = make_mat('dark_red', (0.26, 0.04, 0.03, 1.0))
GOLD = make_mat('gold_window', (0.36, 0.19, 0.04, 1.0), 0.6)
YELLOW = make_mat('imperial_yellow', (0.82, 0.44, 0.03, 1.0), 0.45)
YELLOW2 = make_mat('yellow_ridge', (0.78, 0.38, 0.02, 1.0), 0.45)
PLAZA = make_mat('plaza_stone', (0.55, 0.54, 0.51, 1.0))
PLAZA2 = make_mat('plaza_band', (0.48, 0.47, 0.45, 1.0))
GROUND = make_mat('ground_far', (0.42, 0.43, 0.42, 1.0))

# ---------- helpers ----------
def box(name, cx, cy, z0, z1, sx, sy, mat, rotz=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(cx, cy, (z0 + z1) / 2))
    o = bpy.context.active_object
    o.name = name
    o.scale = (sx, sy, z1 - z0)
    if rotz:
        o.rotation_euler = (0, 0, rotz)
    bpy.ops.object.transform_apply(scale=True)
    if rotz:
        bpy.ops.object.transform_apply(rotation=True)
    o.data.materials.append(mat)
    return o

def hip_roof(name, cx, cy, z_eave, z_top, w_bot, d_bot, w_top, d_top, mat):
    """Frustum hip roof: bottom rect (eaves) -> smaller top rect."""
    hb, db = w_bot / 2, d_bot / 2
    ht, dt = w_top / 2, d_top / 2
    verts = [
        (cx - hb, cy - db, z_eave), (cx + hb, cy - db, z_eave),
        (cx + hb, cy + db, z_eave), (cx - hb, cy + db, z_eave),
        (cx - ht, cy - dt, z_top), (cx + ht, cy - dt, z_top),
        (cx + ht, cy + dt, z_top), (cx - ht, cy + dt, z_top),
    ]
    faces = [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7), (4, 5, 6, 7)]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    mesh.materials.append(mat)
    # upturned eave corners: small tilted slabs at the 4 eave corners
    for i, (sx, sy) in enumerate([(-1, -1), (1, -1), (1, 1), (-1, 1)]):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(cx + sx * (hb - 0.8), cy + sy * (db - 0.8), z_eave + 0.55))
        o = bpy.context.active_object
        o.name = name + '_corner%d' % i
        o.scale = (3.2, 3.2, 0.5)
        o.rotation_euler = (sy * math.radians(22), -sx * math.radians(22), 0)
        bpy.ops.object.transform_apply(scale=True)
        o.data.materials.append(mat)
    return obj

def railing(cx, cy, w, d, z_top, mat, posts=True):
    """Simplified balustrade around a rectangle top edge: panels + posts."""
    hw, hd = w / 2 - 0.45, d / 2 - 0.45
    box('rail_f', cx, cy - hd, z_top, z_top + 0.72, w - 0.9, 0.28, mat)
    box('rail_b', cx, cy + hd, z_top, z_top + 0.72, w - 0.9, 0.28, mat)
    box('rail_l', cx - hw, cy, z_top, z_top + 0.72, 0.28, d - 0.9, mat)
    box('rail_r', cx + hw, cy, z_top, z_top + 0.72, 0.28, d - 0.9, mat)
    if posts:
        pts = []
        x = -hw
        while x <= hw + 0.01:
            pts.append((cx + x, cy - hd)); pts.append((cx + x, cy + hd))
            x += 3.4
        y = -hd + 3.4
        while y <= hd - 3.3:
            pts.append((cx - hw, cy + y)); pts.append((cx + hw, cy + y))
            y += 3.4
        for i, (px, py) in enumerate(pts):
            box('post%d' % i, px, py, z_top, z_top + 1.15, 0.42, 0.42, mat)

def stairs_south(cx, cy_edge, z_from, z_to, width, mat):
    """4 steps descending southward (-Y) from a terrace edge."""
    steps = 4
    dz = (z_to - z_from) / steps
    for i in range(steps):
        zt = z_to - dz * i
        box('stair', cx, cy_edge - 0.55 * (i + 0.5), zt - dz, zt, width, 1.1, mat)

# ---------- ground & plaza ----------
box('ground', 0, 0, -2.0, 0.0, 2400, 2400, GROUND)
box('plaza', 0, -70, 0.0, 0.25, 460, 420, PLAZA)          # great outer court slab
box('plaza_band', 0, -32, 0.25, 0.45, 150, 60, PLAZA2)    # raised court band in front

# ---------- three-tier marble terrace (total 8.13, tiers ~2.71 each) ----------
TIER_H = 8.13 / 3
tiers = [(82, 57), (76, 51), (70, 45)]  # bottom -> top
for i, (w, d) in enumerate(tiers):
    z0 = TIER_H * i
    box('terrace%d' % (i + 1), 0, 0, z0, z0 + TIER_H, w, d, TIER_MATS[i])
    # south-centre stairs between tiers and down to ground
    stairs_south(0, -d / 2, z0, z0 + TIER_H, 13, MARBLE2)
railing(0, 0, 70, 45, 8.13, MARBLE2)                       # top-tier balustrade
box('rail2_f', 0, -51 / 2 + 0.45, TIER_H * 2, TIER_H * 2 + 0.72, 75.1, 0.28, MARBLE2)
box('rail2_b', 0, 51 / 2 - 0.45, TIER_H * 2, TIER_H * 2 + 0.72, 75.1, 0.28, MARBLE2)
# (centre ramp removed in round 2: rendered as floating slab with dark seams)

# ---------- hall body: red walls 63.96 x 37, terrace top -> eave line ----------
WALL_Z0, WALL_Z1 = 8.13, 16.6
box('hall_walls', 0, 0, WALL_Z0, WALL_Z1, 63.96, 37, RED)
# roof spring band (dark, under lower eave)
box('eave_band', 0, 0, WALL_Z1, WALL_Z1 + 0.9, 65.5, 38.5, DARKRED)
# south facade: 11 bays -> 10 dark column strips + gold door/window panels
bay = 63.96 / 11
for i in range(10):
    x = -63.96 / 2 + bay * (i + 1)
    box('col_s%d' % i, x, -18.56, WALL_Z0, WALL_Z1, 0.85, 0.22, DARKRED)
for i in range(11):
    x = -63.96 / 2 + bay * (i + 0.5)
    box('door_s%d' % i, x, -18.58, WALL_Z0 + 1.2, WALL_Z0 + 6.4, 3.4, 0.18, GOLD)
# north facade panels (simpler)
for i in range(11):
    x = -63.96 / 2 + bay * (i + 0.5)
    box('door_n%d' % i, x, 18.58, WALL_Z0 + 1.2, WALL_Z0 + 6.4, 3.4, 0.18, GOLD)
# side windows east/west
for s, sx in (('e', 1), ('w', -1)):
    for j in range(4):
        y = -13.5 + j * 9.0
        box('win_%s%d' % (s, j), sx * 32.06, y, WALL_Z0 + 2.0, WALL_Z0 + 5.6, 0.18, 3.0, GOLD)

# ---------- lower eave hip roof (overhang ~3m) ----------
hip_roof('roof_lower', 0, 0, 17.3, 23.1, 71.0, 44.0, 50.0, 19.0, YELLOW)
box('lower_ridge', 0, 0, 23.1, 23.9, 50.0, 3.2, YELLOW2)

# ---------- upper storey band + upper eave hip roof ----------
box('upper_walls', 0, 0, 22.6, 25.4, 47.0, 17.0, RED)
for i in range(9):
    x = -47.0 / 2 + (47.0 / 9) * (i + 0.5)
    box('uwin_s%d' % i, x, -8.58, 23.1, 24.9, 2.8, 0.18, GOLD)
    box('uwin_n%d' % i, x, 8.58, 23.1, 24.9, 2.8, 0.18, GOLD)
hip_roof('roof_upper', 0, 0, 25.2, 31.65, 55.0, 25.0, 33.0, 7.0, YELLOW)
# main ridge + great chiwen (3.4m) at both ends -> top ~35.05
box('main_ridge', 0, 0, 31.65, 32.45, 33.0, 2.6, YELLOW2)
for s, sx in (('l', -1), ('r', 1)):
    box('chiwen_%s' % s, sx * 16.8, 0, 31.65, 35.05, 2.4, 2.2, YELLOW2)
    box('chiwen_top_%s' % s, sx * 16.8, 0, 35.05, 35.35, 1.4, 1.2, YELLOW2)

# ---------- background silhouettes: rear halls (north axis) ----------
def simple_hall(name, cx, cy, w, d, wall_h, roof_h, base_h):
    box(name + '_base', cx, cy, 0.25, base_h, w + 8, d + 8, MARBLE2)
    box(name + '_wall', cx, cy, base_h, base_h + wall_h, w, d, RED)
    hip_roof(name + '_roof', cx, cy, base_h + wall_h + 0.2, base_h + wall_h + roof_h,
             w + 5, d + 5, w * 0.55, d * 0.3, YELLOW)
simple_hall('zhonghe', 0, 62, 30, 30, 6.5, 7.5, 8.13)    # square-ish hall behind
simple_hall('baohe', 0, 108, 42, 24, 7.0, 8.0, 8.13)      # larger hall further north

# ---------- foreground silhouette: Taihemen gate (south, in front) ----------
box('thm_base', 0, -118, 0.25, 4.5, 52, 20, MARBLE2)
box('thm_wall', 0, -118, 4.5, 10.5, 44, 14, RED)
box('thm_door', 0, -125.2, 4.5, 8.6, 6.0, 0.3, DARKRED)
hip_roof('thm_roof', 0, -118, 10.7, 15.2, 49, 18, 30, 6, YELLOW)
box('thm_ridge', 0, -118, 15.2, 15.8, 30, 2.2, YELLOW2)

# ---------- lighting: sun + sky (same recipe as Osaka build) ----------
sun_data = bpy.data.lights.new('sun', type='SUN')
sun_data.energy = 3.4
sun = bpy.data.objects.new('sun', sun_data)
bpy.context.collection.objects.link(sun)
sun.rotation_euler = (math.radians(50), math.radians(10), math.radians(-35))

world = bpy.data.worlds.new('sky')
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes['Background']
bg.inputs[0].default_value = (0.45, 0.68, 0.95, 1.0)
bg.inputs[1].default_value = 0.6

# ---------- camera ----------
def env_vec(key, default):
    v = os.environ.get(key)
    if v:
        return tuple(float(t) for t in v.split(','))
    return default

cam_data = bpy.data.cameras.new('cam')
cam = bpy.data.objects.new('cam', cam_data)
bpy.context.collection.objects.link(cam)
cam.location = env_vec('TAIHE_CAM', (70, -130, 75))
target = Vector(env_vec('TAIHE_TGT', (0, 0, 25)))
direction = target - Vector(cam.location)
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
cam_data.lens = float(os.environ.get('TAIHE_LENS', 40))
scene.camera = cam

# ---------- render settings ----------
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 64
scene.cycles.use_denoising = True
scene.view_settings.view_transform = 'Standard'
scene.render.resolution_x = 1280
scene.render.resolution_y = 720
scene.render.filepath = OUT
scene.render.image_settings.file_format = 'PNG'
if BLEND:
    bpy.ops.wm.save_as_mainfile(filepath=BLEND)
bpy.ops.render.render(write_still=True)
print('RENDERED', OUT, os.path.getsize(OUT))
