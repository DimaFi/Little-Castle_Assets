import bpy, math, random, os
from mathutils import Vector
random.seed(17)
OUT = os.path.dirname(os.path.abspath(__file__))
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
def mat(name, color):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF'); bs.inputs['Base Color'].default_value=(*color,1); bs.inputs['Roughness'].default_value=.83
    return m
plaster=mat('Warm ivory plaster',(.72,.63,.44)); wood=mat('Honey oak',(.23,.115,.047)); dark=mat('Recess shadow',(.055,.038,.023)); stone=mat('Warm limestone',(.39,.37,.30)); door=mat('Oak door and shutters',(.36,.20,.085)); iron=mat('Dark iron',(.07,.075,.065))
roofm=[mat('Terracotta %02d'%i,(.38+i*.018,.135+i*.009,.065+i*.004)) for i in range(5)]
assets=[]
def cube(name, loc, scale, material, bevel=.04):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc); o=bpy.context.object; o.name=name; o.dimensions=scale; bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    o.data.materials.append(material)
    if bevel:
        mod=o.modifiers.new('Soft edges','BEVEL'); mod.width=bevel; mod.segments=2
        mod=o.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
    assets.append(o); return o
def beam(name,a,b,width,material=wood):
    a,b=Vector(a),Vector(b); o=cube(name,(a+b)/2,(width,width,(b-a).length),material,.025); o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler(); return o
cube('House plaster volume',(0,0,1.85),(5,4,2.9),plaster,.09)
cube('Foundation',(0,0,.25),(5.16,4.16,.5),stone,.07)
# Solid triangular gables, with a roof that reads clearly from strategy distance.
verts=[(-2.5,-2,3.3),(2.5,-2,3.3),(0,-2,5),(-2.5,2,3.3),(2.5,2,3.3),(0,2,5)]
mesh=bpy.data.meshes.new('Gable mesh'); mesh.from_pydata(verts,[],[(0,2,1),(3,4,5),(0,1,4,3),(1,2,5,4),(2,0,3,5)]); mesh.update()
o=bpy.data.objects.new('Plastered gables',mesh); bpy.context.collection.objects.link(o); o.data.materials.append(plaster); assets.append(o)
for x in [-2.48,2.48]:
    for y in [-2.025,2.025]: cube('Corner post',(x,y,1.93),(.17,.17,2.85),wood)
for y in [-2.055,2.055]:
    cube('Front rear crossbeam',(0,y,3.23),(5.12,.16,.19),wood)
    cube('Base timber',(0,y,.62),(5.1,.13,.16),wood)
    beam('Gable timber',(-2.5,y,3.35),(0,y,5),.16); beam('Gable timber',(0,y,5),(2.5,y,3.35),.16)
    beam('Gable upright',(0,y,3.3),(0,y,4.94),.15)
for x in [-2.54,2.54]: cube('Side crossbeam',(x,0,3.22),(.15,4.15,.18),wood)
# Broad overlapping shingles: deliberately limited detail, all exportable geometry.
for side in [-1,1]:
    angle=side*math.atan2(1.8,2.95)
    o=cube('Roof backing',(side*1.475,0,4.08),(3.46,4.75,.10),roofm[1],.035); o.rotation_euler[1]=angle
    for row in range(7):
        x=.22+row*.425; z=5.16-x*(1.8/2.95)
        for col in range(10):
            y=-2.16+col*.48+(row%2)*.035
            o=cube('Roof shingle',(side*x,y,z+random.uniform(-.012,.012)),(.57,.455,.085),random.choice(roofm),.045)
            o.rotation_euler[1]=angle+random.uniform(-.012,.012)
for i in range(10): cube('Ridge cap',(0,-2.16+i*.48,5.15),(.29,.49,.19),roofm[2],.09)
cube('Chimney',(-1.48,.85,4.68),(.62,.68,2.0),stone,.05)
cube('Chimney crown',(-1.48,.85,5.69),(.78,.83,.18),stone,.05)
cube('Chimney dark opening',(-1.48,.85,5.789),(.45,.50,.025),dark,.015)
cube('Door recess',(.65,-2.065,1.42),(1.18,.10,1.98),dark,.06)
for i in range(5): cube('Door plank',(.21+i*.22,-2.13,1.40),(.207,.10,1.85),door,.018)
for x in [.035,1.265]: cube('Door jamb',(x,-2.16,1.43),(.16,.22,2.1),wood)
cube('Door lintel',(.65,-2.16,2.48),(1.42,.23,.2),wood)
for z in [.88,1.87]: cube('Door strap',(.65,-2.192,z),(1.02,.025,.065),iron,.008)
cube('Door handle',(1.0,-2.23,1.40),(.06,.065,.16),iron,.015)
for i in range(2): cube('Entrance step',(.65,-2.42-i*.30,.32-i*.13),(1.65,.62,.22),stone,.045)
def window(x,y,z,side=False):
    before=len(assets)
    cube('Window recess',(x,y,z),(.94,.12,1.05),dark,.045)
    for dx in [-.52,.52]: cube('Window upright',(x+dx,y-.07,z),(.12,.16,1.21),wood)
    for dz in [-.55,.55]: cube('Window horizontal',(x,y-.08,z+dz),(1.16,.18,.12),wood)
    cube('Window mullion',(x,y-.085,z),(.07,.12,1.0),wood,.015)
    cube('Window sill',(x,y-.15,z-.6),(1.28,.34,.12),stone)
    for dx in [-.82,.82]:
        cube('Open shutter',(x+dx,y-.05,z),(.43,.12,1.03),door,.025)
        for dz in [-.34,.34]: cube('Shutter brace',(x+dx,y-.13,z+dz),(.43,.07,.075),wood,.012)
    if side:
        for ob in assets[before:]:
            p=ob.location.copy(); ob.location=(2.56-(p.y-y),p.x-x,z+(p.z-z)); ob.rotation_euler[2]=math.pi/2
window(-1.25,-2.09,1.92)
window(0,0,1.92,True)
for y in [-2.08,2.08]:
    beam('Diagonal brace',(-2.35,y,2.55),(-1.65,y,3.18),.12)
    beam('Diagonal brace',(2.35,y,2.55),(1.7,y,3.18),.12)
# Export only architecture, with house foot at zero and Blender meters converted by FBX.
bpy.ops.object.select_all(action='DESELECT')
for o in assets: o.select_set(True)
bpy.context.view_layer.objects.active=assets[0]
bpy.ops.export_scene.fbx(filepath=os.path.join(OUT,'Cottage_01.fbx'),use_selection=True,object_types={'MESH'},apply_unit_scale=True,axis_forward='-Y',axis_up='Z',use_mesh_modifiers=True,add_leaf_bones=False,bake_anim=False)
# Neutral presentation ground is excluded from FBX.
grass=mat('Preview muted sage',(.21,.29,.15))
cube('Preview ground',(0,0,-.13),(200,200,.2),grass,.0)
world=bpy.context.scene.world; world.use_nodes=True; world.node_tree.nodes['Background'].inputs[0].default_value=(.65,.76,.9,1); world.node_tree.nodes['Background'].inputs[1].default_value=.35
bpy.ops.object.light_add(type='AREA',location=(-3,-5,10)); bpy.context.object.data.energy=1700; bpy.context.object.data.shape='DISK'; bpy.context.object.data.size=7
bpy.context.object.rotation_euler=(Vector((0,0,2))-bpy.context.object.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(10,-14,10)); cam=bpy.context.object; cam.rotation_euler=(Vector((0,0,2.35))-cam.location).to_track_quat('-Z','Y').to_euler(); cam.data.type='ORTHO'; cam.data.ortho_scale=10.4
scene=bpy.context.scene; scene.camera=cam; scene.render.engine='CYCLES'; scene.cycles.samples=32; scene.cycles.use_denoising=True; scene.render.resolution_x=1200; scene.render.resolution_y=1000; scene.render.resolution_percentage=100
scene.world.color=(.3,.3,.3); scene.view_settings.view_transform='AgX'; scene.render.image_settings.file_format='PNG'
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'Cottage_01.blend'))
scene.render.filepath=os.path.join(OUT,'Cottage_01_preview.png'); bpy.ops.render.render(write_still=True)
print('COTTAGE_COMPLETE',len(assets)-1,'architecture objects')
