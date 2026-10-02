import bpy, math, os
from mathutils import Vector
OUT=os.path.dirname(os.path.abspath(__file__))
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
def mat(name,c,metal=0):
    m=bpy.data.materials.new(name);m.diffuse_color=(*c,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Roughness'].default_value=.65;p.inputs['Metallic'].default_value=metal;return m
oak=mat('Warm aged oak',(.38,.215,.08)); edge=mat('Oak end grain',(.24,.125,.045)); slate=mat('Weathered blue green roof',(.13,.23,.23)); dark=mat('Dark interior',(.018,.012,.007)); iron=mat('Aged bronze iron',(.08,.09,.055),.7); glass=mat('Warm amber glass',(.65,.38,.09))
p=glass.node_tree.nodes.get('Principled BSDF');p.inputs['Emission Color'].default_value=(1,.52,.14,1);p.inputs['Emission Strength'].default_value=.45
parts=[]
def box(name,loc,size,m,b=.008):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m)
    if b:md=o.modifiers.new('Rounded handmade edges','BEVEL');md.width=b;md.segments=3
    parts.append(o);return o
def cylinder(name,loc,r,depth,m,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=r,depth=depth,location=loc,rotation=rot);o=bpy.context.object;o.name=name;o.data.materials.append(m);parts.append(o);md=o.modifiers.new('Soft edges','BEVEL');md.width=.003;md.segments=2;return o
def mesh(name,v,f,m):
    me=bpy.data.meshes.new(name);me.from_pydata(v,[],f);me.update();o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);o.data.materials.append(m);parts.append(o);return o
def finish_asset(label,origin):
    bpy.ops.object.select_all(action='DESELECT')
    for o in parts:o.select_set(True)
    bpy.context.view_layer.objects.active=parts[0]
    for o in parts:o.location-=Vector(origin)
    bpy.ops.object.convert(target='MESH');bpy.ops.object.join();o=bpy.context.object;o.name='SM_'+label;bpy.context.scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.mesh.normals_make_consistent(inside=False);bpy.ops.uv.smart_project(island_margin=.02);bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,label+'.blend'))
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUT,label+'.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Y',axis_up='Z',mesh_smooth_type='FACE',bake_anim=False)
    return o
# Birdhouse: actual hollow body and pierced face, not a black circle decal.
box('Mounting backboard',(0,.14,.01),(.085,.035,.58),edge)
box('Back',(0,.11,.02),(.30,.035,.36),oak)
for x in [-.14,.14]:box('Side wall',(x,0,.02),(.025,.24,.36),oak)
box('Floor',(0,0,-.16),(.32,.27,.025),edge)
front=box('Pierced front',(0,-.12,.02),(.30,.028,.36),oak)
bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=.046,depth=.14,location=(0,-.12,.08),rotation=(math.pi/2,0,0));cut=bpy.context.object
bpy.context.view_layer.objects.active=front;mod=front.modifiers.new('Real entrance hole','BOOLEAN');mod.operation='DIFFERENCE';mod.object=cut;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cut,do_unlink=True)
mesh('Front gable',[(-.15,-.135,.20),(.15,-.135,.20),(0,-.135,.37),(-.15,-.11,.20),(.15,-.11,.20),(0,-.11,.37)],[(0,2,1),(3,4,5),(0,1,4,3),(1,2,5,4),(2,0,3,5)],oak)
for side in [-1,1]:
    for row in range(3):
        x=side*(.04+row*.065);z=.392-abs(x)*.98
        for col in range(3):
            o=box('Overlapping slate',(x,-.15+col*.135,z),(.11,.15,.018),slate,.004);o.rotation_euler[1]=side*math.pi/4
    o=box('Roof rake',(side*.103,-.175,.245),(.292,.025,.033),edge,.004);o.rotation_euler[1]=side*math.pi/4
cylinder('Round perch',(0,-.205,-.065),.012,.18,edge,(math.pi/2,0,0))
box('Bottom projecting ledge',(0,-.035,-.18),(.36,.32,.035),oak)
for x in [-.11,.11]:
    for z in [-.12,.16]:cylinder('Forged nail',(x,-.138,z),.006,.006,iron,(math.pi/2,0,0))
bird=finish_asset('Birdhouse_01',(0,.16,0))
# Isolate next native file; birdhouse remains saved above.
bpy.data.objects.remove(bird,do_unlink=True);parts=[]
# Lantern: tapered box with a pitched hood, cage bars and suspension loop.
box('Lantern base',(0,0,-.32),(.18,.18,.035),iron)
box('Lantern upper rim',(0,0,-.075),(.20,.20,.025),iron)
for x in [-.077,.077]:
    for y in [-.077,.077]:box('Cage upright',(x,y,-.20),(.014,.014,.24),iron,.003)
for y in [-.077,.077]:box('Amber front back',(0,y,-.20),(.14,.004,.21),glass,.001)
for x in [-.077,.077]:box('Amber side',(x,0,-.20),(.004,.14,.21),glass,.001)
mesh('Sloped metal hood',[(-.115,-.115,-.065),(.115,-.115,-.065),(.115,.115,-.065),(-.115,.115,-.065),(-.045,-.045,.025),(.045,-.045,.025),(.045,.045,.025),(-.045,.045,.025)],[(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7),(3,2,1,0)],iron)
cylinder('Hood finial',(0,0,.035),.018,.025,iron)
bpy.ops.mesh.primitive_torus_add(major_radius=.034,minor_radius=.005,major_segments=32,minor_segments=8,location=(0,0,.077),rotation=(math.pi/2,0,0));o=bpy.context.object;o.name='Hanging eye';o.data.materials.append(iron);parts.append(o)
lamp=finish_asset('Lantern_01',(0,0,.111))
# Render both separate assets under identical neutral lighting.
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True;scene.render.resolution_x=1000;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[1].default_value=.5
bpy.ops.object.light_add(type='AREA',location=(-1,-2,3));bpy.context.object.data.energy=200;bpy.context.object.data.size=2
bpy.context.object.rotation_euler=(Vector((0,0,0))-bpy.context.object.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add();cam=bpy.context.object;scene.camera=cam;cam.data.type='ORTHO'
for label,obj,target,scale in [('Lantern_01',lamp,(0,0,-.20),.65)]:
    cam.location=(.8,-1.5,.6);cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;scene.render.filepath=os.path.join(OUT,label+'_preview.png');bpy.ops.render.render(write_still=True)
bpy.data.objects.remove(lamp,do_unlink=True)
with bpy.data.libraries.load(os.path.join(OUT,'Birdhouse_01.blend'),link=False) as (src,dst):dst.objects=['SM_Birdhouse_01']
for o in dst.objects:bpy.context.collection.objects.link(o)
cam.location=(.8,-1.5,.6);cam.rotation_euler=(Vector((0,-.1,.1))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.88;scene.render.filepath=os.path.join(OUT,'Birdhouse_01_preview.png');bpy.ops.render.render(write_still=True)
