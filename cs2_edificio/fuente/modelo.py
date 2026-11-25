"""Construye el edificio en Blender (bpy) y exporta FBX para Cities: Skylines II.
Uso: python modelo.py <carpeta_salida> <nombre_malla> [render.png]
Unidades: metros. Parcela 2x3 celdas (16 m de ancho x 24 m de fondo), centrada en el origen.
La fachada principal mira hacia -Y en Blender (lado de la calle)."""
import sys, math, bpy, bmesh

OUT, NAME = sys.argv[1], sys.argv[2]
RENDER = sys.argv[3] if len(sys.argv) > 3 else None
bpy.ops.wm.read_factory_settings(use_empty=True)

# celdas del atlas 4x4 -> (u0, v0, u1, v1) con margen de 4 px
def cell(c, r, pad=4 / 2048):
    return (c / 4 + pad, 1 - (r + 1) / 4 + pad, (c + 1) / 4 - pad, 1 - r / 4 - pad)
WIN, BALC, SHOP, DOOR = cell(0, 0), cell(1, 0), cell(2, 0), cell(3, 0)
WALL, STONE, ROOF, TRIM = cell(0, 1), cell(1, 1), cell(2, 1), cell(3, 1)
RAIL, METAL, SLAB = cell(0, 2), cell(1, 2), cell(2, 2)

class Mesh:
    def __init__(s):
        s.bm = bmesh.new(); s.uv = s.bm.loops.layers.uv.new('UVMap')
    def quad(s, p0, u, v, uvr, tile=(1, 1)):
        """Cuadrilátero desde p0 con lados u y v (vectores). Normal = u x v."""
        pts = [p0, add(p0, u), add(add(p0, u), v), add(p0, v)]
        f = s.bm.faces.new([s.bm.verts.new(p) for p in pts])
        u0, v0, u1, v1 = uvr
        for lp, (a, b) in zip(f.loops, [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]):
            lp[s.uv].uv = (a, b)
    def box(s, x0, y0, z0, x1, y1, z1, uvr, bottom=False, top_uv=None):
        dx, dy, dz = x1 - x0, y1 - y0, z1 - z0
        s.quad((x0, y0, z0), (dx, 0, 0), (0, 0, dz), uvr)            # -Y
        s.quad((x1, y1, z0), (-dx, 0, 0), (0, 0, dz), uvr)           # +Y
        s.quad((x1, y0, z0), (0, dy, 0), (0, 0, dz), uvr)            # +X
        s.quad((x0, y1, z0), (0, -dy, 0), (0, 0, dz), uvr)           # -X
        s.quad((x0, y0, z1), (dx, 0, 0), (0, dy, 0), top_uv or uvr)  # arriba
        if bottom: s.quad((x0, y1, z0), (dx, 0, 0), (0, -dy, 0), uvr)
    def obj(s, name, mat):
        me = bpy.data.meshes.new(name); s.bm.normal_update(); s.bm.to_mesh(me); s.bm.free()
        me.materials.append(mat)
        o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o)
        return o

def add(a, b): return (a[0] + b[0], a[1] + b[1], a[2] + b[2])

# --- dimensiones ---
W, D = 15.0, 15.0              # huella del edificio
X0, Y0 = -W / 2, -12.0 + 0.5    # 0,5 m de retranqueo respecto a la acera
GF, FL, NF = 3.5, 3.0, 4        # planta baja, altura de planta, nº de plantas altas
H = GF + FL * NF                # 15,5 m
MOD = 3.0
cols = int(W / MOD)

def facades(m, detail=True):
    """Cuatro fachadas: frente (-Y), derecha (+X), fondo (+Y), izquierda (-X)."""
    sides = [((X0, Y0), (1, 0)), ((X0 + W, Y0), (0, 1)), ((X0 + W, Y0 + D), (-1, 0)), ((X0, Y0 + D), (0, -1))]
    for si, ((sx, sy), (ux, uy)) in enumerate(sides):
        for c in range(cols):
            p = (sx + ux * c * MOD, sy + uy * c * MOD)
            u = (ux * MOD, uy * MOD, 0)
            if si == 0: g = DOOR if c == cols // 2 else SHOP
            else: g = STONE if si != 2 else (DOOR if c == 1 else STONE)
            m.quad((p[0], p[1], 0), u, (0, 0, GF), g)
            for f in range(NF):
                z = GF + f * FL
                if si == 0: g = BALC if c % 2 else WIN
                elif si == 2: g = WIN
                else: g = WIN if c % 2 == 0 else WALL
                m.quad((p[0], p[1], z), u, (0, 0, FL), g)

def roof(m, detail=True):
    m.quad((X0, Y0, H), (W, 0, 0), (0, D, 0), ROOF)
    if not detail: return
    t, ph = 0.25, 1.0
    m.box(X0 - .05, Y0 - .05, H, X0 + W + .05, Y0 + t, H + ph, TRIM)
    m.box(X0 - .05, Y0 + D - t, H, X0 + W + .05, Y0 + D + .05, H + ph, TRIM)
    m.box(X0 - .05, Y0 + t, H, X0 + t, Y0 + D - t, H + ph, TRIM)
    m.box(X0 + W - t, Y0 + t, H, X0 + W + .05, Y0 + D - t, H + ph, TRIM)
    m.box(X0 + 8.5, Y0 + 7.5, H, X0 + 12, Y0 + 11.5, H + 2.6, WALL, top_uv=SLAB)   # caja de escalera
    m.box(X0 + 8.4, Y0 + 7.4, H + 2.6, X0 + 12.1, Y0 + 11.6, H + 2.8, TRIM)
    for i, (ax, ay) in enumerate([(2, 3), (3.6, 3), (2, 10), (3.6, 10), (5.2, 10)]):
        m.box(X0 + ax, Y0 + ay, H, X0 + ax + 1.0, Y0 + ay + .7, H + .8, METAL)       # aires acondicionados
    m.box(X0 + 10, Y0 + 2, H, X0 + 12.5, Y0 + 4.5, H + .4, TRIM)                     # base depósito
    m.box(X0 + 10.3, Y0 + 2.3, H + .4, X0 + 12.2, Y0 + 4.2, H + 2.0, METAL)          # depósito de agua

def details(m):
    # impostas: banda sobre la planta baja y cornisa superior
    m.box(X0 - .15, Y0 - .15, GF - .1, X0 + W + .15, Y0 + D + .15, GF + .2, TRIM)
    m.box(X0 - .3, Y0 - .3, H - .3, X0 + W + .3, Y0 + D + .3, H, TRIM, bottom=True)
    # balcones de la fachada principal
    for f in range(NF):
        z = GF + f * FL
        for c in range(1, cols, 2):
            cx = X0 + c * MOD + MOD / 2; bw, bd = 2.6, 1.1
            m.box(cx - bw / 2, Y0 - bd, z, cx + bw / 2, Y0, z + .16, SLAB, bottom=True)
            rz, rt = z + .16, .05
            m.box(cx - bw / 2, Y0 - bd, rz, cx + bw / 2, Y0 - bd + rt, rz + 1.0, RAIL)
            m.box(cx - bw / 2, Y0 - bd + rt, rz, cx - bw / 2 + rt, Y0, rz + 1.0, RAIL)
            m.box(cx + bw / 2 - rt, Y0 - bd + rt, rz, cx + bw / 2, Y0, rz + 1.0, RAIL)
    # toldos de los locales
    for c in range(cols):
        if c == cols // 2: continue
        x = X0 + c * MOD
        m.box(x + .35, Y0 - .9, 2.75, x + MOD - .35, Y0, 2.85, METAL, bottom=True)

# --- material ---
mat = bpy.data.materials.new(NAME); mat.use_nodes = True
nt = mat.node_tree; bsdf = nt.nodes['Principled BSDF']
def tex(kind, cs):
    n = nt.nodes.new('ShaderNodeTexImage'); n.image = bpy.data.images.load(f"{OUT}/{NAME}_{kind}.png")
    n.image.colorspace_settings.name = cs; return n
bc = tex('BaseColor', 'sRGB'); nm = tex('Normal', 'Non-Color'); mk = tex('MaskMap', 'Non-Color')
nt.links.new(bc.outputs['Color'], bsdf.inputs['Base Color'])
nmap = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(nm.outputs['Color'], nmap.inputs['Color']); nt.links.new(nmap.outputs['Normal'], bsdf.inputs['Normal'])
sep = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(mk.outputs['Color'], sep.inputs['Color'])
nt.links.new(sep.outputs['Red'], bsdf.inputs['Metallic'])
inv = nt.nodes.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1
nt.links.new(mk.outputs['Alpha'], inv.inputs[1]); nt.links.new(inv.outputs[0], bsdf.inputs['Roughness'])

# --- LOD0 y LOD1 ---
m0 = Mesh(); facades(m0); roof(m0); details(m0); lod0 = m0.obj(NAME, mat)
m1 = Mesh(); facades(m1); roof(m1, detail=False); m1.box(X0, Y0, H, X0 + W, Y0 + D, H + 1.0, TRIM); lod1 = m1.obj(NAME + '_LOD1', mat)

def export(o, path):
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, apply_unit_scale=True, apply_scale_options='FBX_SCALE_ALL',
                             axis_forward='-Z', axis_up='Y', bake_space_transform=True, mesh_smooth_type='FACE',
                             path_mode='STRIP', embed_textures=False, add_leaf_bones=False)
export(lod0, f"{OUT}/{NAME}.fbx"); export(lod1, f"{OUT}/{NAME}_LOD1.fbx")
for o in (lod0, lod1):
    print(o.name, 'triángulos:', sum(len(p.vertices) - 2 for p in o.data.polygons))

if RENDER:
    lod1.hide_render = True
    sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.samples = 48; sc.cycles.device = 'CPU'
    sc.render.resolution_x, sc.render.resolution_y = 1400, 1050
    sc.view_settings.view_transform = 'AgX'
    gm = bpy.data.meshes.new('suelo'); bm = bmesh.new()
    for x0, y0, x1, y1, colr in [(-40, -40, 40, 40, (.32, .45, .22, 1)), (-8, -12, 8, 12, (.55, .55, .52, 1)), (-40, -20, 40, -14, (.12, .12, .13, 1)), (-40, -14, 40, -12, (.6, .6, .58, 1))]:
        pass
    def flat(x0, y0, x1, y1, z, colr):
        me = bpy.data.meshes.new('f'); me.from_pydata([(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)], [], [(0, 1, 2, 3)])
        mm = bpy.data.materials.new('m'); mm.use_nodes = True; mm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = colr
        mm.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = .9
        me.materials.append(mm); o = bpy.data.objects.new('f', me); bpy.context.collection.objects.link(o)
    flat(-60, -60, 60, 60, -.02, (.25, .38, .17, 1)); flat(-8, -12, 8, 12, -.01, (.5, .5, .47, 1))
    flat(-60, -21, 60, -14, 0, (.08, .08, .09, 1)); flat(-60, -14, 60, -12, .0, (.62, .6, .56, 1))
    sun = bpy.data.lights.new('sol', 'SUN'); sun.energy = 4.0; sun.angle = math.radians(2)
    so = bpy.data.objects.new('sol', sun); so.rotation_euler = (math.radians(50), 0, math.radians(-35)); bpy.context.collection.objects.link(so)
    world = bpy.data.worlds.new('w'); world.use_nodes = True; world.node_tree.nodes['Background'].inputs['Color'].default_value = (.55, .7, .9, 1)
    world.node_tree.nodes['Background'].inputs['Strength'].default_value = .9; sc.world = world
    cam = bpy.data.cameras.new('cam'); cam.lens = 42; co = bpy.data.objects.new('cam', cam); bpy.context.collection.objects.link(co)
    co.location = (-24, -42, 20); tgt = (0, -4, 6.5)
    import mathutils
    d = mathutils.Vector(tgt) - mathutils.Vector(co.location); co.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    sc.camera = co; sc.render.filepath = RENDER; bpy.ops.render.render(write_still=True)
    print('render listo')
