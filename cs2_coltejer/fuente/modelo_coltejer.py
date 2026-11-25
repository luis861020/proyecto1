"""Edificio Coltejer (Medellín) para Cities: Skylines II: modelo y exportación FBX con 3 LOD.
Uso: python modelo_coltejer.py <carpeta> <nombre> [prefijo_render]
Metros, origen en el centro de la parcela de 6 x 6 celdas (48 x 48 m). La fachada principal mira a -Y (Blender).
175 m y 36 plantas son datos publicados. La forma (fuste, ensanche de la base y remate cóncavo con ojo)
y la huella (42,7 x 47,6 m) salen de una captura de un modelo 3D de referencia (301,1 mm = 175 m)."""
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
METAL, GRASS, REDL = R(3072, 3072, 1024, 512), R(3072, 3584, 512, 512), R(3584, 3584, 256, 256)
FLAG_CO, FLAG_ANT = R(3840, 3600, 256, 168, 1), R(3584, 3860, 256, 168, 1)

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

# ---------- dimensiones (escala de la referencia: 301,1 mm = 175 m -> 0,581 m/mm) ----------
BX, BY = 42.7, 47.6                       # huella en la base (73,4 x 81,9 mm)
SX, SY = 32.0, 37.0                       # fuste de la torre
X0, X1, Y0, Y1 = -SX / 2, SX / 2, -SY / 2, SY / 2
GH, FT = 6.0, 26.0                        # planta baja y fin del ensanche curvo
FH, NFT = 3.84, 31                        # 31 plantas tipo (+ 5 en la base = 36)
HC0, HC1 = FT + FH * NFT, 175.0           # arranque del remate (145 m) y punta
TC = .55                                  # parte del remate sin ojo / con ojo
FIN_D, FIN_W, SP_D, SPH = .7, .3, .25, 1.0
curve = lambda t: HC0 + (HC1 - HC0) * t * t       # perfil cóncavo del remate, de la fachada (t=0) a la trasera (t=1)
yat = lambda t: Y0 + SY * t

def sides_of(x0, y0, x1, y1):
    return [((x0, y0), (1, 0), (0, -1), x1 - x0), ((x1, y0), (0, 1), (1, 0), y1 - y0),
            ((x1, y1), (-1, 0), (0, 1), x1 - x0), ((x0, y1), (0, -1), (-1, 0), y1 - y0)]

def base(m, lod):
    """Planta baja vertical + ensanche cóncavo que se estrecha hasta el fuste."""
    bx0, by0 = -BX / 2, -BY / 2
    for si, ((px, py), (ux, uy), _, w) in enumerate(sides_of(bx0, by0, -bx0, -by0)):
        nb = 1 if lod == 2 else max(1, round(w / 6))
        bw = w / nb
        for i in range(nb):
            m.quad((px + ux * i * bw, py + uy * i * bw, 0), (ux * bw, uy * bw, 0), (0, 0, GH), SHOP if (i + si) % 4 else GRAN)
    n = [10, 5, 1][lod]
    rings = []
    for k in range(n + 1):
        s = k / n; o = (1 - s) ** 2
        hx, hy = SX / 2 + (BX - SX) / 2 * o, SY / 2 + (BY - SY) / 2 * o
        rings.append([(-hx, -hy, GH + (FT - GH) * s), (hx, -hy, GH + (FT - GH) * s), (hx, hy, GH + (FT - GH) * s), (-hx, hy, GH + (FT - GH) * s)])
    for k in range(n):
        lo, hi = rings[k], rings[k + 1]
        for j in range(4):
            a, b = lo[j], lo[(j + 1) % 4]; c, d = hi[(j + 1) % 4], hi[j]
            v0 = FIN[1] + (FIN[3] - FIN[1]) * k / n; v1 = FIN[1] + (FIN[3] - FIN[1]) * (k + 1) / n
            out = [(0, -1, .3), (1, 0, .3), (0, 1, .3), (-1, 0, .3)][j]
            m.face([a, b, c, d], [(FIN[0], v0), (FIN[2], v0), (FIN[2], v1), (FIN[0], v1)], out)
    if lod == 0:  # marquesinas de acceso en los laterales (en el frente no cabe: la base llega al borde de la parcela)
        for x, sg in ((-BX / 2, -1), (BX / 2, 1)):
            m.box((x, -5, 4.6), (x + sg * 2.2, 5, 5.0), METAL, bottom=True)

def shaft(m, lod):
    for si, ((px, py), (ux, uy), (nx, ny), w) in enumerate(sides_of(X0, Y0, X1, Y1)):
        side = si % 2 == 1
        strips, bays = (SHORT, 23) if side else (LONG, 20)
        if lod == 2:
            m.quad((px, py, FT), (ux * w, uy * w, 0), (0, 0, HC0 - FT), strips[0])
        else:
            for f in range(NFT):
                z = FT + f * FH
                m.quad((px, py, z + SPH), (ux * w, uy * w, 0), (0, 0, FH - SPH), strips[(f * 5 + si * 3) % 8])
                if lod == 0:
                    a = (px + nx * SP_D, py + ny * SP_D, z)
                    m.quad(a, (ux * w, uy * w, 0), (0, 0, SPH), SPAND)
                    m.quad((a[0], a[1], z + SPH), (ux * w, uy * w, 0), (-nx * SP_D, -ny * SP_D, 0), SPAND)
                else:
                    m.quad((px, py, z), (ux * w, uy * w, 0), (0, 0, SPH), SPAND)
        if lod == 0:  # estrías verticales continuas; en los laterales suben siguiendo la curva del remate
            for i in range(1, bays):
                t = i / bays; cx, cy = px + ux * w * t, py + uy * w * t
                if si == 0: top = HC0 + .8
                elif si == 2: top = HC1
                else:
                    tt = (cy - Y0) / SY; top = curve(tt) - .1
                    if .86 < tt < .975: top = HC0   # deja libre el ojo
                a = (cx - ux * FIN_W / 2, cy - uy * FIN_W / 2, FT)
                b = (cx + ux * FIN_W / 2 + nx * FIN_D, cy + uy * FIN_W / 2 + ny * FIN_D, top)
                m.box(a, b, FIN)
    if lod < 2:
        for cx, cy, top in [(X0, Y0, HC0 + .8), (X1, Y0, HC0 + .8), (X1, Y1, HC1), (X0, Y1, HC1)]:
            m.box((cx - .8, cy - .8, FT), (cx + .8, cy + .8, top), FIN)
        m.box((X0 - .3, Y0 - .35, HC0 - .2), (X1 + .3, Y0 + .3, HC0 + .8), SPAND)    # cornisa frontal

def vesica(zb, zt, hw, n, yc):
    L, zm = (zt - zb) / 2, (zt + zb) / 2; Rr = (L * L + hw * hw) / (2 * hw); f0 = math.asin(L / Rr); cx = hw - Rr
    right = [(cx + Rr * math.cos(-f0 + 2 * f0 * k / n), zm + Rr * math.sin(-f0 + 2 * f0 * k / n)) for k in range(n + 1)]
    pts = right + [(-x, z) for x, z in reversed(right[1:-1])]
    return [(yc + x, z) for x, z in pts]

def ray_hit(poly, o, d):
    best = None
    for i in range(len(poly)):
        (ax, az), (bx, bz) = poly[i], poly[(i + 1) % len(poly)]
        ex, ez = bx - ax, bz - az; den = d[0] * ez - d[1] * ex
        if abs(den) < 1e-12: continue
        t = ((ax - o[0]) * ez - (az - o[1]) * ex) / den; u = ((ax - o[0]) * d[1] - (az - o[1]) * d[0]) / den
        if t > 0 and -1e-9 <= u <= 1 + 1e-9 and (best is None or t < best): best = t
    return (o[0] + d[0] * best, o[1] + d[1] * best)

def crown(m, lod):
    """Remate en punta de aguja: el techo sube en curva cóncava de la fachada (145 m) a la trasera (175 m).
    Cerca de la punta, un ojo alargado lo atraviesa de lado a lado."""
    uvx = lambda y, z: (NEEDLE[0] + (y - Y0) / SY * (NEEDLE[2] - NEEDLE[0]), NEEDLE[1] + (z - HC0) / (HC1 - HC0) * (NEEDLE[3] - NEEDLE[1]))
    def xfaces(pts):
        for x, want in ((X0, (-1, 0, 0)), (X1, (1, 0, 0))):
            q = [(x, y, z) for y, z in pts]
            if len({(round(a[1], 4), round(a[2], 4)) for a in q}) < 3: continue
            uniq = []
            for p in q:
                if not uniq or (abs(p[1] - uniq[-1][1]) + abs(p[2] - uniq[-1][2])) > 1e-6: uniq.append(p)
            if len(uniq) > 1 and abs(uniq[0][1] - uniq[-1][1]) + abs(uniq[0][2] - uniq[-1][2]) < 1e-6: uniq.pop()
            m.face(uniq, [uvx(p[1], p[2]) for p in uniq], want)
    def roof_strip(y0, z0, y1, z1):
        u0, u1 = NEEDLE[0], NEEDLE[2]; va, vb = uvx(y0, z0)[1], uvx(y1, z1)[1]
        m.face([(X0, y0, z0), (X1, y0, z0), (X1, y1, z1), (X0, y1, z1)], [(u0, va), (u1, va), (u1, vb), (u0, vb)], (0, -(z1 - z0), (y1 - y0)))
    nf = [24, 10, 6][lod]
    tc = TC if lod < 2 else 1.0
    for k in range(nf):   # parte delantera, maciza
        t0, t1 = tc * k / nf, tc * (k + 1) / nf
        y0, y1, z0, z1 = yat(t0), yat(t1), curve(t0), curve(t1)
        xfaces([(y0, HC0), (y1, HC0), (y1, z1), (y0, z0)]); roof_strip(y0, z0, y1, z1)
    if lod == 2:
        m.quad((X1, Y1, HC0), (-SX, 0, 0), (0, 0, HC1 - HC0), NEEDLE); return
    # parte trasera con el ojo: anillo entre el contorno exterior y el ojo
    yc = Y1 - 3.0
    eye = vesica(HC0 + 4.5, HC0 + 21.5, 1.6, [32, 12][lod], yc)
    nt = 30
    outer = [(yat(tc), HC0), (Y1, HC0), (Y1, HC1)] + [(yat(1 - (1 - tc) * k / nt), curve(1 - (1 - tc) * k / nt)) for k in range(1, nt + 1)]
    o = (yc, HC0 + 13.0); n = [96, 32][lod]
    ang = [-math.pi / 2 + 2 * math.pi * k / n for k in range(n)]
    po = [ray_hit(outer, o, (math.cos(a), math.sin(a))) for a in ang]
    pi = [ray_hit(eye, o, (math.cos(a), math.sin(a))) for a in ang]
    for k in range(n):
        a, b, c, d = po[k], po[(k + 1) % n], pi[(k + 1) % n], pi[k]
        xfaces([a, b, c, d])
        # paredes del ojo
        mid = ((d[0] + c[0]) / 2 - o[0], (d[1] + c[1]) / 2 - o[1])
        va, vb = uvx(*d)[1], uvx(*c)[1]
        m.face([(X0, d[0], d[1]), (X1, d[0], d[1]), (X1, c[0], c[1]), (X0, c[0], c[1])],
               [(NEEDLE[0], va), (NEEDLE[2], va), (NEEDLE[2], vb), (NEEDLE[0], vb)], (0, -mid[0], -mid[1]))
        # paredes exteriores: techo curvo y fachada trasera (no la base ni el corte interior)
        if abs(a[1] - HC0) < 1e-6 and abs(b[1] - HC0) < 1e-6: continue
        if abs(a[0] - yat(tc)) < 1e-6 and abs(b[0] - yat(tc)) < 1e-6: continue
        if abs(a[0] - Y1) < 1e-6 and abs(b[0] - Y1) < 1e-6:
            m.face([(X1, a[0], a[1]), (X0, a[0], a[1]), (X0, b[0], b[1]), (X1, b[0], b[1])],
                   [(NEEDLE[0], uvx(*a)[1]), (NEEDLE[2], uvx(*a)[1]), (NEEDLE[2], uvx(*b)[1]), (NEEDLE[0], uvx(*b)[1])], (0, 1, 0)); continue
        y0, z0, y1, z1 = (a[0], a[1], b[0], b[1]) if a[0] < b[0] else (b[0], b[1], a[0], a[1])
        roof_strip(y0, z0, y1, z1)
    if lod == 0:  # baliza roja y pararrayos en la punta
        m.box((-.4, Y1 - .9, HC1), (.4, Y1 - .1, HC1 + .7), REDL)
        m.box((-.08, Y1 - .58, HC1 + .7), (.08, Y1 - .42, HC1 + 2.5), METAL)

def flags(m, lod):
    """Astas con las banderas de Colombia y de Antioquia en la plazoleta, a ambos lados de la fachada principal."""
    for x, fl in ((-22.7, FLAG_CO), (22.7, FLAG_ANT)):
        y, ph = -21.0, 16.0
        m.box((x - .45, y - .45, 0), (x + .45, y + .45, .5), GRAN)                       # pedestal
        m.box((x - .09, y - .09, .5), (x + .09, y + .09, ph), METAL)                       # asta
        if lod == 0: m.box((x - .14, y - .14, ph), (x + .14, y + .14, ph + .25), METAL)  # remate
        # tela: 3 x 2 m, ondulada, hacia +Y (dentro de la parcela) y por las dos caras
        nseg = 10 if lod == 0 else 3; fw, fh = 4.5, 3.0; z1 = ph - .15
        pts = [(x + (.45 * math.sin(math.pi * 1.6 * k / nseg) * (k / nseg)) * (1 if lod == 0 else 0), y + .07 + fw * k / nseg) for k in range(nseg + 1)]
        for k in range(nseg):
            (xa, ya), (xb, yb) = pts[k], pts[k + 1]
            ua = fl[0] + (fl[2] - fl[0]) * k / nseg; ub = fl[0] + (fl[2] - fl[0]) * (k + 1) / nseg
            quad = [(xa, ya, z1 - fh), (xb, yb, z1 - fh), (xb, yb, z1), (xa, ya, z1)]
            uv = [(ua, fl[1]), (ub, fl[1]), (ub, fl[3]), (ua, fl[3])]
            m.face(quad, uv, (1, 0, 0)); m.face(quad, uv, (-1, 0, 0))

def plaza(m):
    m.quad((-24, -24, .02), (24 - BX / 2, 0, 0), (0, 48, 0), PAVE)
    m.quad((BX / 2, -24, .02), (24 - BX / 2, 0, 0), (0, 48, 0), PAVE)
    for x in (-22.6, 22.6):
        for y in (-14, 0, 14): m.box((x - .7, y - 2, 0), (x + .7, y + 2, .6), GRAN, top=GRASS)

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
    m = Mesh(); base(m, lod); shaft(m, lod); crown(m, lod)
    if lod < 2: plaza(m); flags(m, lod)
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
    shot(RENDER + '_dia.png', (-130, -170, 40), (0, 0, 85), 30, (1000, 1400))
    shot(RENDER + '_aguja.png', (-95, -30, 168), (0, 4, 152), 40, (1200, 1200))
    shot(RENDER + '_banderas.png', (0, -78, 9), (0, -18, 13), 26, (1400, 1000))
    shot(RENDER + '_noche.png', (150, -150, 30), (0, 0, 85), 30, (1000, 1400), night=True)
    print('render listo')
