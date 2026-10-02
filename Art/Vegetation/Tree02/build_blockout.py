"""Tree02 stage 1 only. Run in Blender 4.4 with -- --revision v001 --views Front,Perspective.
Writes only inside Tree02; never runs the old kit's generator.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

import bpy
import bmesh
from mathutils import Vector

args = argparse.ArgumentParser()
args.add_argument('--revision', default='v001')
args.add_argument('--views', default='Front,Back,Left,Right,Top,Bottom,Perspective,Gameplay,Wood')
opt = args.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
assert opt.revision.isalnum()
ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[2]
OUT = ROOT/'Source'/opt.revision
RENDERS = ROOT/'Renders'/opt.revision
QA = ROOT/'QA'/opt.revision
for p in (OUT, RENDERS, QA):
    p.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1

def collection(name, parent=None):
    c = bpy.data.collections.new(name)
    (parent or scene.collection).children.link(c)
    return c

tree = collection('01_TREE02_BLOCKOUT')
wood_col = collection('Wood', tree)
canopy = collection('Canopy_Proxies_NOT_FINAL_LEAVES', tree)
source = collection('02_EDITABLE_GROWTH_SOURCE')
trunk_src = collection('Trunk', source)
roots_src = collection('Roots', source)
branches_src = collection('Branches', source)
stones = collection('03_OPTIONAL_STONES_FROM_OAK_KIT')
refs = collection('80_REFERENCES')
studio = collection('90_PREVIEW_NOT_FOR_EXPORT')

def put(obj, col):
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    col.objects.link(obj)
    return obj

def active(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.hide_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

def material(name, color):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    bs = m.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value = (*color, 1)
    bs.inputs['Roughness'].default_value = .88
    bs.inputs['Specular IOR Level'].default_value = .18
    return m

bark = material('BLOCKOUT_Wood_NoTexture', (.34, .18, .075))
leaf = material('BLOCKOUT_Canopy_NoLeaves', (.37, .46, .085))
floor_mat = material('PREVIEW_Background', (.70, .68, .61))

def interpolate(points, radii, steps=5):
    ps = [Vector(p) for p in points]
    samples, rr = [], []
    for i in range(len(ps)-1):
        p0, p1, p2, p3 = ps[max(i-1,0)], ps[i], ps[i+1], ps[min(i+2,len(ps)-1)]
        for k in range(steps):
            t = k/steps
            samples.append(.5*(2*p1+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t*t*t))
            rr.append(radii[i]*(1-t)+radii[i+1]*t)
    return samples+[ps[-1]], rr+[radii[-1]]

parts = []
def tube(name, points, radii, col, sides=16, flatten=1):
    ps, rs = interpolate(points, radii)
    verts, faces = [], []
    prev = None
    for i, (c,r) in enumerate(zip(ps,rs)):
        axis = (ps[min(i+1,len(ps)-1)]-ps[max(i-1,0)]).normalized()
        side = axis.cross(Vector((0,1,0))).normalized() if prev is None else (prev-axis*prev.dot(axis)).normalized()
        other = axis.cross(side).normalized()
        prev = side
        for j in range(sides):
            a = math.tau*j/sides
            ridge = 1 + .065*math.sin(5*a+i*.085) + .035*math.cos(3*a-i*.06)
            p = c + r*ridge*(math.cos(a)*side+math.sin(a)*other)
            p.z = c.z+(p.z-c.z)*flatten
            verts.append(p)
    for i in range(len(ps)-1):
        for j in range(sides):
            a=i*sides+j; b=i*sides+(j+1)%sides
            faces.append((a,b,b+sides,a+sides))
    faces += [tuple(reversed(range(sides))), tuple((len(ps)-1)*sides+j for j in range(sides))]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    bm=bmesh.new(); bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces)); bm.to_mesh(mesh); bm.free()
    obj = bpy.data.objects.new(name,mesh); col.objects.link(obj)
    mesh.materials.append(bark)
    for p in mesh.polygons: p.use_smooth = True
    obj['control_points_m'] = [list(p) for p in points]
    obj['control_radii_m'] = radii
    parts.append(obj)
    return obj

# Positions are hand-directed from the primary reference, not random growth.
tube('SRC_Trunk_S_Curve', [(0,0,-.15),(-.18,.02,.4),(-.43,.06,.95),(-.42,.10,1.45),(-.12,.08,1.95),(.29,.05,2.48),(.40,.09,2.97),(.36,.12,3.38),(.65,.19,3.94),(1.03,.26,4.50)], [.55,.51,.43,.37,.33,.285,.225,.18,.13,.035], trunk_src,24)
root_specs = [
    ([(-.39,.02,1.12),(-.25,-.15,.77),(.28,-.24,.40),(.74,-.40,.17),(1.36,-.49,-.015),(1.76,-.55,-.10)],[.25,.29,.28,.20,.085,.012]),
    ([(-.24,-.10,1.11),(-.13,-.39,.57),(.27,-.72,.20),(.55,-1.04,-.05)],[.25,.26,.16,.012]),
    ([(-.38,-.05,.65),(-.53,-.39,.30),(-.90,-.68,.11),(-1.19,-.82,-.07)],[.29,.235,.14,.014]),
    ([(-.29,.08,.6),(-.74,.12,.29),(-1.10,.31,.08),(-1.38,.43,-.08)],[.30,.21,.11,.012]),
    ([(-.08,.13,.70),(.12,.48,.31),(.66,.81,.12),(1.10,1.05,-.07)],[.28,.23,.13,.012]),
    ([(-.23,.14,.55),(-.44,.58,.28),(-.47,1.0,.08),(-.28,1.35,-.07)],[.27,.20,.105,.012]),
    ([(.0,.08,.5),(.44,.12,.25),(.99,.30,.10),(1.33,.57,-.08)],[.30,.22,.115,.012])]
for i,(p,r) in enumerate(root_specs): tube('SRC_Root_%02d'%(i+1),p,r,roots_src,16,.74)

branch_specs = [
    ('A_Left',[(-.34,.06,1.50),(-.72,.03,2.09),(-1.13,.02,2.40),(-1.30,-.03,3.04)],[.29,.245,.18,.04]),
    ('B_Central',[(.02,.08,2.20),(.10,.02,2.78),(-.11,-.07,3.24),(-.19,-.13,3.85)],[.27,.205,.145,.025]),
    ('C_High',[(.36,.13,3.21),(.75,.18,3.69),(1.35,.22,4.02),(1.55,.22,4.51)],[.195,.17,.11,.025]),
    ('D_MidRight',[(.18,.04,2.25),(.67,.01,2.79),(1.17,.0,2.95),(1.40,.10,3.27)],[.235,.19,.12,.025]),
    ('E_OuterRight',[(.20,.01,2.34),(.79,-.03,2.57),(1.25,-.02,2.38),(1.78,.0,2.46),(2.10,.01,2.73)],[.22,.18,.13,.085,.018]),
    ('F_LowFront',[(-.24,-.03,1.55),(.14,-.36,1.78),(.58,-.65,2.04),(1.00,-.75,2.19)],[.22,.175,.11,.018]),
    ('G_BackLeft',[(.20,.16,2.58),(-.18,.66,2.98),(-.57,1.0,3.43),(-.65,1.09,3.84)],[.21,.15,.09,.018]),
    ('H_BackHigh',[(.38,.15,3.05),(.79,.71,3.46),(.98,1.05,3.88),(1.02,1.11,4.23)],[.18,.13,.075,.018])]
for name,p,r in branch_specs: tube('SRC_Primary_'+name,p,r,branches_src)
for name,p,r in [
    ('A_Fork',[(-1.04,.01,2.38),(-1.53,.0,2.68),(-1.68,.09,3.03)],[.14,.09,.015]),
    ('B_Fork',[(.02,.02,2.99),(.36,.14,3.35),(.38,.2,3.71)],[.12,.075,.014]),
    ('C_Fork',[(.89,.2,3.88),(1.52,.43,4.07),(1.81,.43,4.32)],[.105,.064,.014])]: tube('SRC_Secondary_'+name,p,r,branches_src,12)

# Keep the intentional underground seating shallow and avoid an exposed stump below grade.
for ob in parts:
    for v in ob.data.vertices:
        v.co.x *= .96
        if v.co.z < -.08:
            v.co.z = -.08 + (v.co.z+.08)*.18

# Preserve all editable growth parts; merge copies into a continuous preview surface.
copies=[]
for ob in parts:
    cp=ob.copy();cp.data=ob.data.copy();wood_col.objects.link(cp);copies.append(cp)
bpy.ops.object.select_all(action='DESELECT')
for ob in copies: ob.select_set(True)
bpy.context.view_layer.objects.active=copies[0]
bpy.ops.object.join()
wood=bpy.context.object;wood.name='SM_Tree02_Wood_Blockout'
mod=wood.modifiers.new('Continuous_root_and_branch_junctions','REMESH');mod.mode='VOXEL';mod.voxel_size=.032
bpy.ops.object.modifier_apply(modifier=mod.name)
mod=wood.modifiers.new('Gentle_junction_smoothing','SMOOTH');mod.factor=.62;mod.iterations=4
bpy.ops.object.modifier_apply(modifier=mod.name)
mod=wood.modifiers.new('Blockout_density','DECIMATE');mod.ratio=.36
bpy.ops.object.modifier_apply(modifier=mod.name)
for poly in wood.data.polygons: poly.use_smooth=True
wood['stage']='Blockout. No final topology or UV.'
source.hide_render=True;source.hide_viewport=True

masses = [
    ('A_Left',(-1.16,-.02,3.02),(.99,.72,.77)),
    ('B_Central',(-.14,-.06,3.90),(.85,.69,.70)),
    ('C_High',(1.19,.23,4.53),(.91,.73,.76)),
    ('D_MidRight',(1.34,.13,3.17),(.54,.53,.49)),
    ('E_OuterRight',(2.16,.02,2.65),(.51,.47,.46)),
    ('F_LowFront',(.90,-.73,2.05),(.74,.56,.54)),
    ('G_BackLeft',(-.69,1.06,3.66),(.68,.61,.61)),
    ('H_BackHigh',(1.03,1.12,4.13),(.62,.55,.55))]
for idx,(name,center,scale) in enumerate(masses):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=16,location=center)
    obj=put(bpy.context.object,canopy);obj.name='SM_Tree02_LeafCluster_'+name+'_PROXY'
    for v in obj.data.vertices:
        n=v.co.normalized();az=math.atan2(n.y,n.x)
        # Soft, broad lobes only. These volumes are composition guides, not foliage.
        wave=1+.075*math.sin(3*az+idx*.63)*(1-n.z*n.z)+.04*math.cos(5*az-2*n.z+idx)
        v.co.x*=scale[0]*wave;v.co.y*=scale[1]*wave;v.co.z*=scale[2]*(1+.035*math.sin(4*az+idx))
        v.co.x*=.96
    obj.location.x*=.96
    obj.data.materials.append(leaf)
    for poly in obj.data.polygons: poly.use_smooth=True
    obj['purpose']='Temporary canopy mass; replace with oriented leaf cards after shape review.'
    obj['support_branch']=name

# Append only two authorized stone modules. No old tree, foliage or bark is imported.
old=ROOT.parent/'Oak_Kit/Cozy_Oak_Kit.blend'
old_hash=hashlib.sha256(old.read_bytes()).hexdigest()
names=['SM_Stone_Medium_A','SM_Stone_Small_B']
with bpy.data.libraries.load(str(old),link=False) as (src,dst):
    assert all(n in src.objects for n in names)
    dst.objects=list(names)
for obj,pos in zip(dst.objects,[(-1.02,-.65,.0),(.66,-1.12,.0)]):
    stones.objects.link(obj);obj.location=pos;obj.hide_render=False;obj.hide_viewport=False;obj.hide_set(False)
    obj['source_blend']=str(old);obj['source_module']=obj.name
    obj.name='OPTIONAL_'+obj.name
stones.hide_render=True;stones.hide_viewport=True

# Pack the primary reference as a disabled viewport image for later matching.
reference=PROJECT/'Mat/TZ_Tree2/Стилизованное дерево с цветущими корнями.png'
im=bpy.data.images.load(str(reference));im.pack()
empty=bpy.data.objects.new('REF_Primary_Tree02',None);refs.objects.link(empty)
empty.empty_display_type='IMAGE';empty.data=im;empty.empty_display_size=5.2
empty.location=(.25,.9,2.6);empty.rotation_euler=(math.pi/2,0,0)
refs.hide_render=True;refs.hide_viewport=True

bpy.ops.mesh.primitive_plane_add(size=200)
floor=put(bpy.context.object,studio);floor.name='PREVIEW_Floor';floor.data.materials.append(floor_mat)
world=bpy.data.worlds.new('Soft studio');scene.world=world;world.use_nodes=True
world.node_tree.nodes['Background'].inputs[0].default_value=(.74,.79,.86,1)
world.node_tree.nodes['Background'].inputs[1].default_value=.45
for name,pos,power,size,color in [('Key',(-3,-5,9),1100,5,(1,.89,.72)),('Fill',(5,-2,6),650,5,(.82,.9,1)),('Rim',(2,4,8),1000,4,(1,.94,.78))]:
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size;data.color=color
    ob=bpy.data.objects.new(name,data);studio.objects.link(ob);ob.location=pos
    ob.rotation_euler=(Vector((0,0,2.5))-ob.location).to_track_quat('-Z','Y').to_euler()

views={
    'Front':((.25,-16,2.65),(.25,0,2.65),6.2),
    'Back':((.25,16,2.65),(.25,0,2.65),6.2),
    'Left':((-16,0,2.65),(0,0,2.65),6.2),
    'Right':((16,0,2.65),(0,0,2.65),6.2),
    'Top':((.25,0,18),(.25,0,0),6.2),
    'Bottom':((.25,0,-18),(.25,0,0),6.2),
    'Perspective':((6,-16,7.2),(.25,0,2.6),6.5),
    'Gameplay':((7,-11,11),(.25,0,2.6),6.5),
    'Wood':((4,-14,6),(.2,0,2.25),5.6),
    'Stones':((4,-8,4),(.0,-.1,.45),3.5)}
cameras={}
for name,(pos,target,size) in views.items():
    data=bpy.data.cameras.new('CAM_'+name);data.type='ORTHO';data.ortho_scale=size
    ob=bpy.data.objects.new('CAM_'+name,data);studio.objects.link(ob);ob.location=pos
    ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler();cameras[name]=ob
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True
try:
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
    devices=[d for d in prefs.devices if d.type=='OPTIX']
    if devices:
        for d in prefs.devices:d.use=d.type=='OPTIX'
        scene.cycles.device='GPU'
except Exception: pass
scene.render.resolution_x=900;scene.render.resolution_y=900;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.view_settings.view_transform='AgX'
scene.camera=cameras['Perspective']
scene['status']='Tree02 stage 1: shape blockout, not a finished game asset.'
scene['reference_priority']='Primary hero and concept; turnaround is supporting, not an exact blueprint.'
scene['user_scope']='Start with overall form; old-tree stones may be reused.'

# Ensure the saved viewport starts on the useful whole-tree camera.
active(wood)
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_perspective='CAMERA'
            area.spaces.active.shading.type='MATERIAL'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Tree02_Blockout.blend'))

def bounds(objects):
    vs=[o.matrix_world@Vector(c) for o in objects for c in o.bound_box]
    lo=[min(v[i] for v in vs) for i in range(3)];hi=[max(v[i] for v in vs) for i in range(3)]
    return {'min':lo,'max':hi,'dimensions':[hi[i]-lo[i] for i in range(3)]}
bpy.context.view_layer.update()
bm=bmesh.new();bm.from_mesh(wood.data)
nonmanifold=sum(not e.is_manifold for e in bm.edges);bm.free()
manifest={'blender':bpy.app.version_string,'stage':1,'revision':opt.revision,'root_count':7,'primary_branch_count':8,'canopy_mass_count':8,'bounds_m':bounds([wood]+list(canopy.objects)),'wood_triangles':sum(len(p.vertices)-2 for p in wood.data.polygons),'wood_nonmanifold_edges':nonmanifold,'source_parts':len(parts),'stone_source':str(old),'stone_source_sha256':old_hash,'stones':names,'stones_enabled_by_default':False,'reference':str(reference),'not_implemented':['final leaves','UV','final bark and foliage materials','wind','LOD','collision','FBX','engine import'],'render_views':opt.views.split(',')}
(QA/'blockout_report.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print('BLOCKOUT_SAVED',json.dumps(manifest),flush=True)
for name in opt.views.split(','):
    scene.camera=cameras[name]
    floor.hide_render=name in ['Top','Bottom']
    canopy.hide_render=name in ['Wood','Stones']
    stones.hide_render=name!='Stones';stones.hide_viewport=name!='Stones'
    scene.render.filepath=str(RENDERS/(name+'.png'))
    bpy.ops.render.render(write_still=True)
    print('RENDER_DONE',name,flush=True)
assert hashlib.sha256(old.read_bytes()).hexdigest()==old_hash
print('OLD_SOURCE_UNCHANGED',flush=True)
