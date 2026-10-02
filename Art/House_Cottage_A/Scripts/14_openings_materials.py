"""Directional UV/material pass for openings; preserve all grey sources.

Blender 4.4 background: --python this_file -- [modules|house|assembly|validate]
UV0 intentionally reuses texture strips, not a unique bake/lightmap atlas.
"""
import sys, math, json, hashlib
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from kit_geometry import *

ROOT = Path(__file__).resolve().parents[1]
MATROOT = ROOT.parents[1] / 'Mat'
MODULES = ROOT / 'Source/Modules/Openings_Materials_v002'
REND = ROOT / 'Renders/Checkpoint_06/v009'
SCALE = .43  # 1254px source images -> approximately 539 pixels per metre
NAMES = ['SM_Door_Entrance_A', 'SM_Window_Open_A', 'SM_Window_Small_A', 'SM_Window_Closed_A']

def seed(name):
    return int(hashlib.sha256(name.encode()).hexdigest()[:8], 16)

def plain(name, color, roughness, metallic=0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Roughness'].default_value = roughness
    p.inputs['Metallic'].default_value = metallic
    m.diffuse_color = (*color, 1)
    return m

def wood(name, folder, tint, strength):
    m = plain(name, tint, .72)
    n, l = m.node_tree.nodes, m.node_tree.links
    p = n.get('Principled BSDF'); p.location = (650, 80)
    uv = n.new('ShaderNodeUVMap'); uv.uv_map = 'UV0'; uv.location = (-850, 0)
    for i, channel in enumerate(['BaseColor', 'Roughness', 'Normal']):
        path = MATROOT / folder / (folder + '_A_' + channel + '.png')
        im = bpy.data.images.load(str(path), check_existing=True)
        im.colorspace_settings.name = 'sRGB' if channel == 'BaseColor' else 'Non-Color'
        im.pack()
        t = n.new('ShaderNodeTexImage'); t.image = im; t.label = folder + ' / ' + channel
        t.location = (-600, 300 - i * 300); l.new(uv.outputs['UV'], t.inputs['Vector'])
        if channel == 'BaseColor':
            mix = n.new('ShaderNodeMixRGB'); mix.blend_type = 'MIX'; mix.inputs[0].default_value = .24
            mix.inputs[2].default_value = (*tint, 1); mix.location = (0, 300)
            mix.label = 'Soften source contrast, preserve warm timber'
            l.new(t.outputs['Color'], mix.inputs[1]); l.new(mix.outputs[0], p.inputs['Base Color'])
        elif channel == 'Roughness':
            remap = n.new('ShaderNodeMapRange'); remap.location = (0, 0)
            remap.inputs['To Min'].default_value = .55; remap.inputs['To Max'].default_value = .86
            l.new(t.outputs['Color'], remap.inputs['Value']); l.new(remap.outputs[0], p.inputs['Roughness'])
        else:
            normal = n.new('ShaderNodeNormalMap'); normal.uv_map = 'UV0'; normal.location = (0, -260)
            normal.inputs['Strength'].default_value = strength
            l.new(t.outputs['Color'], normal.inputs['Color']); l.new(normal.outputs[0], p.inputs['Normal'])
    m['source'] = str(MATROOT / folder)
    m['uv_note'] = 'UV0: directional strips at 0.43 UV/m. Packed original images.'
    return m

def materials():
    mats = {
        'door': wood('M_Cottage_DoorWood_A', 'DoorWood', (.24, .12, .045), .20),
        'shutter': wood('M_Cottage_ShutterWood_A', 'Shutters', (.30, .17, .065), .16),
        'timber': wood('M_Cottage_FrameWood_A', 'T_Timber', (.19, .10, .040), .15),
        'iron': plain('M_Cottage_ForgedIron_A', (.065, .073, .069), .48, .8),
        'glass': plain('M_Cottage_WindowGlass_Proxy_A', (.045, .085, .085), .22, .12),
        'stone': plain('M_Cottage_Limestone_A', (.54, .43, .28), .88),
    }
    mats['glass']['note'] = 'Opaque exterior proxy: no interior modeled; not transmissive glass.'
    stone = mats['stone']; n, l = stone.node_tree.nodes, stone.node_tree.links
    p = n.get('Principled BSDF')
    tex = n.new('ShaderNodeTexNoise'); tex.inputs['Scale'].default_value = 24
    tex.inputs['Detail'].default_value = 2
    coord = n.new('ShaderNodeTexCoord'); l.new(coord.outputs['Object'], tex.inputs['Vector'])
    bump = n.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = .12
    bump.inputs['Distance'].default_value = .008
    l.new(tex.outputs['Fac'], bump.inputs['Height']); l.new(bump.outputs[0], p.inputs['Normal'])
    info = n.new('ShaderNodeObjectInfo'); mix = n.new('ShaderNodeMixRGB')
    mix.inputs[1].default_value = (.43, .33, .21, 1); mix.inputs[2].default_value = (.62, .51, .34, 1)
    l.new(info.outputs['Random'], mix.inputs[0]); l.new(mix.outputs[0], p.inputs['Base Color'])
    stone['note'] = 'Procedural limestone study, one color variation per geometric stone. No masonry image repeated on blocks.'
    return mats

def projected_uv(o, along=2, horizontal_texture=False, strip=.1):
    """Metric face projection, grain along the specified LOCAL construction axis."""
    me = o.data; uv = me.uv_layers.get('UV0') or me.uv_layers.new(name='UV0')
    lo = [min(v.co[i] for v in me.vertices) for i in range(3)]
    # Physical local dimensions also account for unapplied scale on stone instances.
    scales = [o.matrix_world.to_3x3().col[i].length for i in range(3)]
    for p in me.polygons:
        normal_axis = max(range(3), key=lambda a: abs(p.normal[a]))
        length_axis = along if normal_axis != along else next(a for a in range(3) if a != normal_axis)
        cross_axis = next(a for a in range(3) if a not in (normal_axis, length_axis))
        for li in p.loop_indices:
            v = me.vertices[me.loops[li].vertex_index].co
            length = (v[length_axis] - lo[length_axis]) * scales[length_axis] * SCALE + .045
            cross = (v[cross_axis] - lo[cross_axis]) * scales[cross_axis] * SCALE + strip
            uv.data[li].uv = (length, cross) if horizontal_texture else (cross, length)
    return uv

def swept_uv(o):
    """Ring topology from geometry.beam: arc length and physical perimeter, with one seam."""
    me = o.data; projected_uv(o, horizontal_texture=True)
    uv = me.uv_layers['UV0']; count = len(me.vertices) // 4
    assert len(me.vertices) % 4 == 0 and count >= 2, o.name
    centers = [sum((me.vertices[4*i+j].co for j in range(4)), Vector()) / 4 for i in range(count)]
    arc = [0.0]
    for i in range(1, count): arc.append(arc[-1] + (centers[i]-centers[i-1]).length)
    perimeter = [0.0]
    for j in range(4): perimeter.append(perimeter[-1] + (me.vertices[(j+1)%4].co-me.vertices[j].co).length)
    for p in me.polygons:
        rings = {me.loops[li].vertex_index // 4 for li in p.loop_indices}
        if len(rings) == 1: continue  # caps retain planar UV
        corners = {me.loops[li].vertex_index % 4 for li in p.loop_indices}
        seam = corners == {0, 3}
        for li in p.loop_indices:
            idx = me.loops[li].vertex_index; j = idx % 4
            cross = perimeter[4 if seam and j == 0 else j]
            uv.data[li].uv = (.045 + arc[idx//4]*SCALE, .31 + cross*SCALE)
    o['uv_method'] = 'Arc-length sweep, seam on fourth side; planar end caps'

def assign(objects):
    mats = materials(); records = []
    for o in objects:
        if o.type != 'MESH': continue
        # Single-user mesh preserves original linked grey prototypes elsewhere.
        o.data = o.data.copy(); name = o.name
        if 'Recess' in name:
            key = 'glass'
            # Grey backing previously floated 9 cm behind the wooden rebate.
            # Seat it against the rear of the frame, with 25 mm concealed overlap.
            lo = [min(v.co[i] for v in o.data.vertices) for i in range(3)]
            hi = [max(v.co[i] for v in o.data.vertices) for i in range(3)]
            for v in o.data.vertices:
                v.co.y -= .105
                for axis in [0, 2]:
                    mid = (lo[axis]+hi[axis])/2
                    v.co[axis] = mid + (v.co[axis]-mid)*(1+.05/(hi[axis]-lo[axis]))
            o['glass_seating_fix'] = 'Backing advanced 105 mm; concealed X/Z overlap 25 mm'
        elif any(x in name for x in ['IronStrap', 'Rivet', 'Hinge', 'Handle']): key = 'iron'
        elif 'StoneArch' in name or 'Door_Jamb' in name: key = 'stone'
        elif 'Door_Plank' in name: key = 'door'
        elif 'Shutter_Plank' in name: key = 'shutter'
        else: key = 'timber'
        o.data.materials.clear(); o.data.materials.append(mats[key])
        for p in o.data.polygons: p.material_index = 0
        # Choose grain strips between painted board joints in the source maps.
        strips = [.025, .205, .365, .535, .705, .875] if key == 'door' else [.02, .14, .28, .40, .55, .70, .84]
        strip = strips[seed(name) % len(strips)]
        along = 0 if any(x in name for x in ['Brace', 'Crossbar', 'Sill', 'Strap']) else 2
        projected_uv(o, along, key == 'timber', strip if key != 'timber' else .31)
        if key == 'timber' and any(x in name for x in ['_Arch_', '_Mullion_', 'Dormer_Window_Jamb']): swept_uv(o)
        else: o['uv_method'] = 'Metric local face projection; grain X or Z according to construction'
        o['stage'] = 'OPENINGS MATERIAL STUDY v009; UV0 textured; no lightmap/LOD'
        o['uv_scale_per_m'] = SCALE; o['material_role'] = key
        records.append({'name': name, 'material': key, 'uv_method': o['uv_method']})
    return records

def validate(objects):
    stats = inspect_geometry(objects); assert not stats['issues'], stats
    uv_bad = []; triangles = 0
    for o in objects:
        if o.type != 'MESH': continue
        me = o.data; assert me.uv_layers.get('UV0'), o.name
        assert len(me.materials) == 1 and me.materials[0].name.startswith('M_Cottage_'), o.name
        me.calc_loop_triangles(); uv = me.uv_layers['UV0'].data
        for tri in me.loop_triangles:
            a,b,c = [uv[i].uv for i in tri.loops]; area = abs((b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x)) / 2
            if not math.isfinite(area) or area < 1e-12: uv_bad.append(o.name)
            triangles += 1
    assert not uv_bad, sorted(set(uv_bad))
    stats.update(uv_triangles_checked=triangles, uv_degenerate_faces=0)
    return stats

def shape_fingerprint(objects):
    """Only geometry/hierarchy/pose, excluding intentional UV and material edits."""
    result = {}
    for o in objects:
        value = {'parent': o.parent.name if o.parent else None,
                 'matrix': [list(row) for row in o.matrix_world]}
        if o.type == 'MESH' and 'Recess' not in o.name:
            value['vertices'] = [list(v.co) for v in o.data.vertices]
            value['polygons'] = [list(p.vertices) for p in o.data.polygons]
        result[o.name] = hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()
    return result

def save(target):
    if target.exists(): raise FileExistsError(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    for im in bpy.data.images:
        if im.source == 'FILE' and im.has_data and not im.packed_file: im.pack()
    bpy.ops.wm.save_as_mainfile(filepath=str(target))

def checker(sc, cam, path):
    m = plain('QA_UV_Checker', (.5,.5,.5), .8)
    n,l = m.node_tree.nodes,m.node_tree.links
    uv = n.new('ShaderNodeUVMap'); uv.uv_map = 'UV0'
    ch = n.new('ShaderNodeTexChecker'); ch.inputs['Scale'].default_value = 20
    ch.inputs['Color1'].default_value = (.025,.09,.16,1); ch.inputs['Color2'].default_value = (.65,.8,.8,1)
    l.new(uv.outputs[0],ch.inputs['Vector']);l.new(ch.outputs[0],n.get('Principled BSDF').inputs['Base Color'])
    sc.view_layers[0].material_override = m
    render(sc,cam,path,700)
    sc.view_layers[0].material_override = None

mode = sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'modules'
REND.mkdir(parents=True,exist_ok=True)
report = []
if mode == 'modules':
    for name in NAMES:
        bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Source/Modules/Openings_v002'/name/(name+'.blend')))
        sc = bpy.data.scenes[name]; bpy.context.window.scene = sc
        objects = list(bpy.data.collections[name].all_objects)
        records = assign(objects); stats = validate(objects)
        target = MODULES/name/(name+'.blend'); save(target)
        render(sc,sc.camera,REND/(name+'.png'),800)
        if name in NAMES[:2]: checker(sc,sc.camera,REND/(name+'_UV.png'))
        stats.update(name=name,file=str(target.relative_to(ROOT)),parts=records); report.append(stats)
elif mode in ['house','assembly']:
    source = 'Source/Openings/v007/House_Cottage_A.blend' if mode == 'house' else 'Source/Assembly/v008/Cottage_Courtyard.blend'
    target = ROOT / ('Source/Materials/v009/House_Cottage_A.blend' if mode == 'house' else 'Source/Assembly/v009/Cottage_Courtyard.blend')
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/source)); sc = bpy.context.scene
    objects = list(bpy.data.collections['07_WINDOWS'].all_objects)+list(bpy.data.collections['08_DOORS'].all_objects)
    records = assign(objects); stats = validate(objects)
    stats.update(parts=records,file=str(target.relative_to(ROOT)))
    save(target)
    if mode == 'house':
        for title,camname in [('House_Hero','CAM_01_Hero_Front_Left'),('House_Door','CAM_Door_Detail'),('House_Window','CAM_Window_Detail')]:
            render(sc,bpy.data.objects[camname],REND/(title+'.png'),900)
    else: render(sc,sc.camera,REND/'Courtyard_Hero.png',1100)
    report.append(stats)
elif mode == 'validate':
    for name in NAMES:
        source = ROOT/'Source/Modules/Openings_v002'/name/(name+'.blend')
        bpy.ops.wm.open_mainfile(filepath=str(source)); bpy.context.view_layer.update()
        original = shape_fingerprint(list(bpy.data.collections[name].all_objects))
        target = MODULES/name/(name+'.blend')
        bpy.ops.wm.open_mainfile(filepath=str(target)); sc = bpy.data.scenes[name]; bpy.context.window.scene=sc
        objects=list(bpy.data.collections[name].all_objects); stats=validate(objects)
        bpy.context.view_layer.update()
        assert shape_fingerprint(objects) == original, ('Geometry/pose changed',name)
        images=[im for im in bpy.data.images if im.name.endswith('.png') and any(k in im.name for k in ['DoorWood','Shutters','T_Timber'])]
        assert images and all(im.packed_file for im in images), name
        assert sc.camera and sc.unit_settings.scale_length == 1, name
        stats.update(name=name,packed_images=len(images),non_glass_geometry_and_all_pivots_unchanged=True);report.append(stats)
    for kind,source,target in [
        ('house','Source/Openings/v007/House_Cottage_A.blend','Source/Materials/v009/House_Cottage_A.blend'),
        ('assembly','Source/Assembly/v008/Cottage_Courtyard.blend','Source/Assembly/v009/Cottage_Courtyard.blend')]:
        bpy.ops.wm.open_mainfile(filepath=str(ROOT/source)); bpy.context.view_layer.update()
        original = shape_fingerprint(list(bpy.data.objects))
        bpy.ops.wm.open_mainfile(filepath=str(ROOT/target)); bpy.context.view_layer.update()
        assert shape_fingerprint(list(bpy.data.objects)) == original, ('Geometry/pose changed',kind)
        objects=list(bpy.data.collections['07_WINDOWS'].all_objects)+list(bpy.data.collections['08_DOORS'].all_objects)
        stats=validate(objects); stats.update(name=kind,non_glass_geometry_and_all_pivots_unchanged=True)
        report.append(stats)
else: raise ValueError(mode)
(ROOT/'QA'/('materials_v009_'+mode+'.json')).write_text(json.dumps(report,indent=2),encoding='utf-8')
print('MATERIAL_STAGE_COMPLETE',mode,len(report),flush=True)
