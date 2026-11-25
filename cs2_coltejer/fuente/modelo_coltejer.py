"""Edificio Coltejer (Medellín) para Cities: Skylines II: modelo y exportación FBX con 3 LOD.
Uso: python modelo_coltejer.py <carpeta> <nombre> [prefijo_render]
Metros, origen en el centro de la parcela de 8 x 6 celdas (64 x 48 m). La calle queda en -Y (Blender).
Medidas: 175 m de altura total y 36 plantas son datos publicados. La planta (45 x 20 m), el reparto
de alturas, la aguja y el podio son una interpretación aproximada."""
import sys, math, bpy, bmesh, mathutils

OUT, NAME = sys.argv[1], sys.argv[2]
RENDER = sys.argv[3] if len(sys.argv) > 3 else None
bpy.ops.wm.read_factory_settings(use_empty=True)
S = 4096
def R(x, y, w, h, pad=3):  # rectángulo en píxeles -> (u0, v0, u1, v1)
    return ((x + pad) / S, 1 - (y + h - pad) / S, (x + w - pad) / S, 1 - (y + pad) / S)
LONG = [R(0, v * 128, S, 128) for v in range(8)]
SHORT = [R(0, 1024 + v * 128, S, 128) for v in range(8)]
FIN, SPAND, NEEDLE, ROOF, PAVE = R(0, 2048, 512, 1024), R(512, 2048, 512, 1024), R(1024, 2048, 1024, 1024), R(2048, 2048, 1024, 1024), R(3072, 2048, 1024, 1024)
SHOP, PODWIN, GRAN = R(0, 3072, 1024, 1024), R(1024, 3072, 1024, 1024), R(2048, 3072, 1024, 1024)
METAL, GRASS, REDL = R(3072, 3072, 1024, 512), R(3072, 3584, 512, 512), R(3584, 3584, 512, 512)

V = mathutils.Vector
class Mesh:
    def __init__(s):
        s.bm = bmesh.new(); s.uv = s.bm.loops.layers.uv.new('UVMap')
    def face(s, pts, uvs, want=None):
        pts = [V(p) for p in pts]
        if want is not None:
            n = (pts[1] - pts[0]).cross(pts[2] - pts[0])
            if n.length < 1e-9 and len(pts) > 3: n = (pts[2] - pts[0]).cross(pts[3] - pts[0])
            if n.dot(V(want)) < 0: pts, uvs = pts[::-1], uvs[::-1]
        f = s.bm.faces.new([s.bm.verts.new(p) for p in pts])
        for lp, uv in zip(f.loops, uvs): lp[s.uv].uv = uv
    def quad(s, p0, u, v, r):
        p0, u, v = V(p0), V(u), V(v)
        s.face([p0, p0 + u, p0 + u + v, p0 + v], [(r[0], r[1]), (r[2], r[1]), (r[2], r[3]), (r[0], r[3])])
    def box(s, a, b, r, top=None, bottom=False, sides=True):
        x0, y0, z0 = (min(a[i], b[i]) for i in range(3)); x1, y1, z1 = (max(a[i], b[i]) for i in range(3))
        dx, dy, dz = x1 - x0, y1 - y0, z1 - z0
        if sides:
            s.quad((x0, y0, z0), (dx, 0, 0), (0, 0, dz), r); s.quad((x1, y1, z0), (-dx, 0, 0), (0, 0, dz), r)
            s.quad((x1, y0, z0), (0, dy, 0), (0, 0, dz), r); s.quad((x0, y1, z0), (0, -dy, 0), (0, 0, dz), r)
        s.quad((x0, y0, z1), (dx, 0, 0), (0, dy, 0), top or r)
        if bottom: s.quad((x0, y1, z0), (dx, 0, 0), (0, -dy, 0), r)
    def obj(s, name, mat):
        me = bpy.data.meshes.new(name); s.bm.normal_update(); s.bm.to_mesh(me); s.bm.free(); me.materials.append(mat)
        o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o); return o

# ---------- dimensiones ----------
TW, TD = 45.0, 20.0                       # planta de la torre
TX0, TX1, TY0, TY1 = -TW / 2, TW / 2, 2.0, 22.0
PH = 10.0                                 # podio: 2 plantas de 5 m
FH, NFT = 3.75, 34                        # plantas de la torre (2 + 34 = 36)
H0 = PH + FH * NFT                        # 137,5 m: azotea de la torre
NB, APEX = H0 + 1.8, 175.0                # arranque y punta de la aguja
ND = 12.0                                 # espesor de la aguja
PX0, PX1, PY0, PY1 = -30.0, 30.0, -22.0, 22.0
SPH, FIN_D, FIN_W, SP_D = 1.0, .7, .3, .25

def sides_of(x0, y0, x1, y1):
    """(esquina izquierda vista desde fuera, dirección, normal exterior, ancho) para las 4 caras."""
    return [((x0, y0), (1, 0), (0, -1), x1 - x0), ((x1, y0), (0, 1), (1, 0), y1 - y0),
            ((x1, y1), (-1, 0), (0, 1), x1 - x0), ((x0, y1), (0, -1), (-1, 0), y1 - y0)]

def tower(m, lod):
    for si, ((px, py), (ux, uy), (nx, ny), w) in enumerate(sides_of(TX0, TY0, TX1, TY1)):
        strips = LONG if si % 2 == 0 else SHORT
        bays = 30 if si % 2 == 0 else 13
        if lod == 2:
            m.quad((px, py, PH), (ux * w, uy * w, 0), (0, 0, H0 - PH), strips[0]); continue
        for f in range(NFT):
            z = PH + f * FH
            m.quad((px, py, z + SPH), (ux * w, uy * w, 0), (0, 0, FH - SPH), strips[(f * 5 + si * 3) % 8])
            if lod == 0:  # antepecho saliente
                a = (px + nx * SP_D, py + ny * SP_D, z); b = (px + ux * w + nx * SP_D, py + uy * w + ny * SP_D, z + SPH)
                m.quad(a, (ux * w, uy * w, 0), (0, 0, SPH), SPAND)
                m.quad((a[0], a[1], z + SPH), (ux * w, uy * w, 0), (-nx * SP_D, -ny * SP_D, 0), SPAND)
            else:
                m.quad((px, py, z), (ux * w, uy * w, 0), (0, 0, SPH), SPAND)
        if lod == 0:  # aletas verticales continuas: el rasgo principal de la fachada
            for i in range(1, bays):
                t = w * i / bays
                cx, cy = px + ux * t, py + uy * t
                a = (cx - ux * FIN_W / 2, cy - uy * FIN_W / 2, PH)
                b = (cx + ux * FIN_W / 2 + nx * FIN_D, cy + uy * FIN_W / 2 + ny * FIN_D, H0 + .6)
                m.box(a, b, FIN)
    # pilares de esquina
    if lod < 2:
        for cx, cy in [(TX0, TY0), (TX1, TY0), (TX1, TY1), (TX0, TY1)]:
            m.box((cx - .8, cy - .8, PH), (cx + .8, cy + .8, H0 + 1.8), FIN)
    # azotea y antepecho de coronación
    m.quad((TX0, TY0, H0), (TW, 0, 0), (0, TD, 0), ROOF)
    if lod == 0:
        t = .4
        for a, b in [((TX0 - .3, TY0 - .3, H0), (TX1 + .3, TY0 + t, NB)), ((TX0 - .3, TY1 - t, H0), (TX1 + .3, TY1 + .3, NB)),
                     ((TX0 - .3, TY0, H0), (TX0 + t, TY1, NB)), ((TX1 - t, TY0, H0), (TX1 + .3, TY1, NB))]:
            m.box(a, b, SPAND)
        m.box((TX0 + 3, TY0 + 2, H0), (TX0 + 9, TY0 + 6, H0 + 3), METAL)    # cuarto de máquinas
        m.box((TX1 - 9, TY1 - 6, H0), (TX1 - 3, TY1 - 2, H0 + 3), METAL)

def pointed_arch(s, h, n):
    """Contorno exterior: base recta + arco apuntado (ojival) de luz s y altura h. Origen en la base."""
    c = (h * h - (s / 2) ** 2) / s; r = s / 2 + c
    a1 = math.atan2(h, c)
    right = [(-c + r * math.cos(a1 * k / n), r * math.sin(a1 * k / n)) for k in range(n + 1)]
    left = [(-x, z) for x, z in reversed(right)]
    base = [(s / 2 * (1 - k / 20), 0) for k in range(1, 20)] + [(0, 0)] + [(-s / 2 * k / 20, 0) for k in range(1, 20)]
    return [(0, 0)] + [(s / 2 * k / 20, 0) for k in range(1, 20)] + right + left[1:] + base[20:]

def vesica(zb, zt, hw, n):
    L, zm = (zt - zb) / 2, (zt + zb) / 2; Rr = (L * L + hw * hw) / (2 * hw); f0 = math.asin(L / Rr); cx = hw - Rr
    right = [(cx + Rr * math.cos(-f0 + 2 * f0 * k / n), zm + Rr * math.sin(-f0 + 2 * f0 * k / n)) for k in range(n + 1)]
    return right + [(-x, z) for x, z in reversed(right[1:-1])]

def ray_hit(poly, o, d):
    best = None
    for i in range(len(poly)):
        (ax, az), (bx, bz) = poly[i], poly[(i + 1) % len(poly)]
        ex, ez = bx - ax, bz - az; den = d[0] * ez - d[1] * ex
        if abs(den) < 1e-12: continue
        t = ((ax - o[0]) * ez - (az - o[1]) * ex) / den; u = ((ax - o[0]) * d[1] - (az - o[1]) * d[0]) / den
        if t > 0 and -1e-9 <= u <= 1 + 1e-9 and (best is None or t < best): best = t
    return (o[0] + d[0] * best, o[1] + d[1] * best)

def needle(m, lod):
    """La aguja: un arco apuntado macizo de 45 m de luz con un ojo alargado que lo atraviesa."""
    n = [96, 40, 16][lod]
    outer = [(x, z + NB) for x, z in pointed_arch(TW, APEX - NB, 60)]
    eye = vesica(NB + 9.5, APEX - 6.5, 5.2, 40)
    yc = (TY0 + TY1) / 2; yf, yb = yc - ND / 2, yc + ND / 2
    o = (0.0, (NB + 9.5 + APEX - 6.5) / 2)
    ang = [-math.pi / 2 + 2 * math.pi * k / n for k in range(n)]
    po = [ray_hit(outer, o, (math.cos(a), math.sin(a))) for a in ang]
    pi = [ray_hit(eye, o, (math.cos(a), math.sin(a))) for a in ang]
    uvp = lambda x, z: (NEEDLE[0] + (x + TW / 2) / TW * (NEEDLE[2] - NEEDLE[0]), NEEDLE[1] + (z - NB) / (APEX - NB) * (NEEDLE[3] - NEEDLE[1]))
    for k in range(n):
        a, b, c, d = po[k], po[(k + 1) % n], pi[(k + 1) % n], pi[k]
        for y, want in ((yf, (0, -1, 0)), (yb, (0, 1, 0))):
            m.face([(a[0], y, a[1]), (b[0], y, b[1]), (c[0], y, c[1]), (d[0], y, d[1])], [uvp(*a), uvp(*b), uvp(*c), uvp(*d)], want)
        for p, q, sign in ((a, b, 1), (d, c, -1)):
            mid = ((p[0] + q[0]) / 2 - o[0], 0, (p[1] + q[1]) / 2 - o[1])
            u0, u1 = NEEDLE[0], NEEDLE[0] + (NEEDLE[2] - NEEDLE[0]) * .25
            m.face([(p[0], yf, p[1]), (q[0], yf, q[1]), (q[0], yb, q[1]), (p[0], yb, p[1])],
                   [(u0, uvp(*p)[1]), (u0, uvp(*q)[1]), (u1, uvp(*q)[1]), (u1, uvp(*p)[1])], tuple(sign * v for v in mid))
    if lod == 0:  # luz de balizaje y pararrayos en la punta
        m.box((-.35, yc - .35, APEX - 1.6), (.35, yc + .35, APEX - .9), REDL)
        m.box((-.08, yc - .08, APEX - .9), (.08, yc + .08, APEX), METAL)
        m.box((TX0 + .5, yf - .3, NB - .2), (TX1 - .5, yb + .3, NB + 1.0), SPAND)   # junta entre aguja y torre

def podium(m, lod):
    bay = 6.0
    if lod == 2:
        for (px, py), (ux, uy), _, w in sides_of(PX0, PY0, PX1, PY1):
            m.quad((px, py, 0), (ux * w, uy * w, 0), (0, 0, PH), PODWIN)
        m.quad((PX0, PY0, PH), (PX1 - PX0, 0, 0), (0, PY1 - PY0, 0), ROOF); return
    AY = PY0 + 3.0  # fondo del soportal
    for i in range(10):  # fachada a la calle: locales bajo soportal, ventana corrida arriba
        x = PX0 + i * bay
        m.quad((x, AY, 0), (bay, 0, 0), (0, 0, 5), SHOP)
        m.quad((x, PY0, 5), (bay, 0, 0), (0, 0, 5), PODWIN)
    m.quad((PX0, AY, 5), (PX1 - PX0, 0, 0), (0, -(AY - PY0), 0), SPAND)      # techo del soportal
    for (px, py), (ux, uy), _, w in sides_of(PX0, PY0, PX1, PY1)[1:]:
        nb = max(1, round(w / bay)); bw = w / nb
        for i in range(nb):
            p = (px + ux * i * bw, py + uy * i * bw)
            m.quad((p[0], p[1], 0), (ux * bw, uy * bw, 0), (0, 0, 5), GRAN if i % 3 else SHOP)
            m.quad((p[0], p[1], 5), (ux * bw, uy * bw, 0), (0, 0, 5), PODWIN)
    if lod == 0:
        m.quad((PX0, PY0, 0), (0, AY - PY0, 0), (0, 0, 5), GRAN); m.quad((PX1, AY, 0), (0, -(AY - PY0), 0), (0, 0, 5), GRAN)
        for i in range(11):  # pilares de granito
            x = PX0 + i * bay
            m.box((x - .35, PY0, 0), (x + .35, PY0 + .7, 5), GRAN)
        m.box((PX0 - .25, PY0 - .25, 4.8), (PX1 + .25, PY1 + .25, 5.3), SPAND, bottom=True)     # imposta
        m.box((-6.5, PY0 - 1.8, 4.2), (6.5, PY0 + .1, 4.6), METAL, bottom=True)                    # marquesina de entrada
        for x in (-6.2, 6.2): m.box((x - .1, PY0 - 1.7, 0), (x + .1, PY0 - 1.5, 4.2), METAL)
    m.quad((PX0, PY0, PH), (PX1 - PX0, 0, 0), (0, PY1 - PY0, 0), ROOF)
    t = .35
    for a, b in [((PX0, PY0, PH), (PX1, PY0 + t, PH + 1.1)), ((PX0, PY1 - t, PH), (PX1, PY1, PH + 1.1)),
                 ((PX0, PY0, PH), (PX0 + t, PY1, PH + 1.1)), ((PX1 - t, PY0, PH), (PX1, PY1, PH + 1.1))]:
        m.box(a, b, GRAN)
    if lod == 0:  # terraza del podio: jardineras, claraboyas y bancas
        for x in (-24, -14, 14, 24):
            m.box((x - 3, -16, PH), (x + 3, -12, PH + .8), GRAN, top=GRASS)
        for x in (-20, -6, 8, 20):
            m.box((x - 2, -6, PH), (x + 2, -2, PH + 1.2), METAL)
        for x in (-19, -9, 9, 19):
            m.box((x - 1.2, -19, PH), (x + 1.2, -18.4, PH + .45), SPAND)

def plaza(m):
    m.quad((-32, -24, .02), (64, 0, 0), (0, 2, 0), PAVE)
    m.quad((-32, -22, .02), (2, 0, 0), (0, 46, 0), PAVE); m.quad((30, -22, .02), (2, 0, 0), (0, 46, 0), PAVE)
    m.quad((-32, 22, .02), (64, 0, 0), (0, 2, 0), PAVE)
    for x in (-27, -15, 15, 27): m.box((x - 1, -23.8, 0), (x + 1, -22.6, .6), GRAN, top=GRASS)

# ---------- material ----------
mat = bpy.data.materials.new(NAME); nt = mat.node_tree; bsdf = nt.nodes['Principled BSDF']
def tex(kind, cs):
    n = nt.nodes.new('ShaderNodeTexImage'); n.image = bpy.data.images.load(f"{OUT}/{NAME}_{kind}.png"); n.image.colorspace_settings.name = cs; return n
bc, nm, mk, em = tex('BaseColor', 'sRGB'), tex('Normal', 'Non-Color'), tex('MaskMap', 'Non-Color'), tex('Emissive', 'sRGB')
nt.links.new(bc.outputs['Color'], bsdf.inputs['Base Color'])
nmap = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(nm.outputs['Color'], nmap.inputs['Color']); nt.links.new(nmap.outputs['Normal'], bsdf.inputs['Normal'])
sep = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(mk.outputs['Color'], sep.inputs['Color']); nt.links.new(sep.outputs['Red'], bsdf.inputs['Metallic'])
inv = nt.nodes.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1
nt.links.new(mk.outputs['Alpha'], inv.inputs[1]); nt.links.new(inv.outputs[0], bsdf.inputs['Roughness'])
nt.links.new(em.outputs['Color'], bsdf.inputs['Emission Color']); bsdf.inputs['Emission Strength'].default_value = 0

objs = []
for lod in range(3):
    m = Mesh(); tower(m, lod); needle(m, lod); podium(m, lod)
    if lod < 2: plaza(m)
    objs.append(m.obj(NAME + ('' if lod == 0 else f'_LOD{lod}'), mat))

for o in objs:
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
    bpy.ops.export_scene.fbx(filepath=f"{OUT}/{o.name}.fbx", use_selection=True, apply_unit_scale=True, apply_scale_options='FBX_SCALE_ALL',
                             axis_forward='-Z', axis_up='Y', bake_space_transform=True, mesh_smooth_type='FACE',
                             path_mode='STRIP', embed_textures=False, add_leaf_bones=False)
    bb = [o.matrix_world @ V(c) for c in o.bound_box]
    print(o.name, 'triángulos:', sum(len(p.vertices) - 2 for p in o.data.polygons), 'caja:', [round(min(v[i] for v in bb), 1) for i in range(3)], [round(max(v[i] for v in bb), 1) for i in range(3)])

if RENDER:
    for o in objs[1:]: o.hide_render = True
    sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.samples = 40; sc.cycles.device = 'CPU'; sc.view_settings.view_transform = 'AgX'
    def flat(x0, y0, x1, y1, z, c):
        me = bpy.data.meshes.new('f'); me.from_pydata([(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)], [], [(0, 1, 2, 3)])
        mm = bpy.data.materials.new('m'); mm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = c
        mm.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = .9; me.materials.append(mm)
        o = bpy.data.objects.new('f', me); bpy.context.collection.objects.link(o)
    flat(-3000, -3000, 3000, 3000, -.03, (.28, .36, .2, 1)); flat(-32, -24, 32, 24, -.01, (.45, .44, .41, 1))
    flat(-3000, -33, 3000, -26, 0, (.07, .07, .08, 1)); flat(-3000, -26, 3000, -24, 0, (.55, .53, .5, 1))
    sun = bpy.data.lights.new('sol', 'SUN'); sun.angle = math.radians(1.5); so = bpy.data.objects.new('sol', sun); bpy.context.collection.objects.link(so)
    world = bpy.data.worlds.new('w'); bg = world.node_tree.nodes['Background']; sc.world = world
    cam = bpy.data.cameras.new('cam'); co = bpy.data.objects.new('cam', cam); bpy.context.collection.objects.link(co); sc.camera = co
    def shot(path, loc, tgt, lens, res, night=False):
        cam.lens = lens; co.location = loc; co.rotation_euler = (V(tgt) - V(loc)).to_track_quat('-Z', 'Y').to_euler()
        sc.render.resolution_x, sc.render.resolution_y = res
        sun.energy = .03 if night else 4.2; so.rotation_euler = (math.radians(52), 0, math.radians(-38))
        bg.inputs['Color'].default_value = (.02, .03, .07, 1) if night else (.55, .7, .92, 1); bg.inputs['Strength'].default_value = .5 if night else .9
        bsdf.inputs['Emission Strength'].default_value = 4.0 if night else 0
        sc.render.filepath = path; bpy.ops.render.render(write_still=True)
    shot(RENDER + '_dia.png', (-120, -190, 45), (0, 0, 82), 30, (1000, 1400))
    shot(RENDER + '_aguja.png', (-55, -80, 150), (0, 12, 150), 45, (1200, 1200))
    shot(RENDER + '_noche.png', (95, -200, 30), (0, 0, 85), 30, (1000, 1400), night=True)
    print('render listo')
