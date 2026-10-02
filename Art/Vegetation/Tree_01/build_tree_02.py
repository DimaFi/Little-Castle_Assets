"""CozySettlement hero tree v2.

Creates a presentation tree plus Unity-ready LOD meshes. Existing assets are read only.
Blender 4.4+, deterministic.
"""
import bpy, math, random, os
from mathutils import Vector

OUT = os.path.dirname(os.path.abspath(__file__))
SEED = 2909
rng = random.Random(SEED)

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for datablocks in (bpy.data.materials, bpy.data.curves, bpy.data.meshes):
    pass

def mat(name, color, rough=.75, metallic=0.0):
    m=bpy.data.materials.new(name); m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Roughness'].default_value=rough
    p.inputs['Metallic'].default_value=metallic
    return m

def bark_material():
    m=mat('M_Tree02_Bark',(0.285,0.135,0.055),.86)
    n=m.node_tree.nodes; l=m.node_tree.links; p=n.get('Principled BSDF')
    tex=n.new('ShaderNodeTexNoise'); tex.inputs['Scale'].default_value=3.3; tex.inputs['Detail'].default_value=2.2; tex.inputs['Roughness'].default_value=.55
    mapping=n.new('ShaderNodeMapping'); coord=n.new('ShaderNodeTexCoord')
    mapping.inputs['Scale'].default_value=(5.0,5.0,.48)
    ramp=n.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position=.25; ramp.color_ramp.elements[0].color=(.045,.012,.003,1)
    ramp.color_ramp.elements[1].position=.74; ramp.color_ramp.elements[1].color=(.40,.19,.075,1)
    bump=n.new('ShaderNodeBump'); bump.inputs['Strength'].default_value=.38; bump.inputs['Distance'].default_value=.12
    l.new(coord.outputs['Generated'],mapping.inputs['Vector']); l.new(mapping.outputs['Vector'],tex.inputs['Vector'])
    l.new(tex.outputs['Fac'],ramp.inputs['Fac']); l.new(ramp.outputs['Color'],p.inputs['Base Color'])
    l.new(tex.outputs['Fac'],bump.inputs['Height']); l.new(bump.outputs['Normal'],p.inputs['Normal'])
    return m

BARK=bark_material()
LEAVES=[mat('M_Leaf_%02d'%i,c,.78) for i,c in enumerate([
    (.18,.31,.055),(.25,.40,.075),(.34,.48,.10),(.42,.53,.13),(.13,.25,.045),(.50,.57,.17)])]
for m in LEAVES:
    p=m.node_tree.nodes.get('Principled BSDF'); p.inputs['Specular IOR Level'].default_value=.18
    p.inputs['Subsurface Weight'].default_value=.035
WOOD=mat('M_Birdhouse_WarmWood',(.42,.22,.075),.76)
ROOF=mat('M_Birdhouse_Roof',(.15,.25,.25),.64)
IRON=mat('M_Lantern_AgedIron',(.045,.052,.038),.48,.72)
GLASS=mat('M_Lantern_WarmGlass',(.62,.24,.035),.30)
gp=GLASS.node_tree.nodes.get('Principled BSDF'); gp.inputs['Emission Color'].default_value=(1.0,.22,.025,1); gp.inputs['Emission Strength'].default_value=3.0
DARK=mat('M_DeepRecess',(.008,.004,.002),.95)
GROUND=mat('M_PreviewGround',(.21,.28,.12),.92)

wood_parts=[]
def curve_branch(name, points, radii, resolution=2):
    cu=bpy.data.curves.new(name,'CURVE'); cu.dimensions='3D'; cu.resolution_u=resolution; cu.bevel_resolution=2; cu.resolution_u=3
    sp=cu.splines.new('BEZIER'); sp.bezier_points.add(len(points)-1)
    for bp,p,rad in zip(sp.bezier_points,points,radii):
        bp.co=p; bp.radius=rad; bp.handle_left_type='AUTO'; bp.handle_right_type='AUTO'
    cu.bevel_depth=1.0; cu.resolution_u=3
    ob=bpy.data.objects.new(name,cu); bpy.context.collection.objects.link(ob); ob.data.materials.append(BARK); wood_parts.append(ob); return ob

# Broad, readable trunk with an early fork and asymmetric handmade silhouette.
curve_branch('Trunk_Main',[(0,0,-.18),(.02,0,.35),(-.10,.02,1.20),(.08,.04,2.05),(.18,.08,2.72),(-.08,.10,3.35),(-.48,.12,4.05),(-.78,.15,4.78)], [.72,.66,.56,.49,.42,.32,.20,.035])
curve_branch('Trunk_Right',[(.08,.03,1.55),(.42,.08,2.25),(.92,.10,3.0),(1.30,.06,3.88),(1.12,.12,4.82),(.78,.18,5.72)],[.43,.37,.30,.22,.12,.025])
curve_branch('Limb_Left',[(-.02,.01,2.20),(-.65,-.06,2.82),(-1.42,-.16,3.32),(-2.22,-.12,3.82),(-2.82,-.04,4.35)],[.33,.29,.22,.14,.025])
curve_branch('Limb_Back',[(.12,.10,2.46),(.15,.72,3.12),(-.05,1.38,3.78),(-.52,1.92,4.55)],[.29,.23,.14,.02])
curve_branch('Limb_Right',[(.54,.04,2.62),(1.32,-.28,3.2),(2.05,-.50,3.82),(2.65,-.48,4.35)],[.26,.21,.12,.02])

# Grounded radial roots: thick at trunk, taper and sink beneath the ground.
for i in range(9):
    a=i*math.tau/9 + rng.uniform(-.10,.10); length=rng.uniform(1.05,1.85)
    d=Vector((math.cos(a),math.sin(a),0)); side=Vector((-d.y,d.x,0))
    pts=[d*.08+Vector((0,0,.30)), d*.48+side*rng.uniform(-.10,.10)+Vector((0,0,.17)), d*length*.78+side*rng.uniform(-.13,.13)+Vector((0,0,.045)), d*length+Vector((0,0,-.16))]
    curve_branch('Root_%02d'%i,[tuple(x) for x in pts],[.34,.25,.10,.018])

# Major twig network and canopy anchors.
anchors=[]
limb_specs=[((-2.75,-.04,4.32),(-3.25,.15,4.85)),((-.75,.15,4.72),(-1.30,.25,5.45)),((.78,.18,5.68),(.60,.18,6.25)),((2.62,-.48,4.32),(3.05,-.32,4.80)),((-.50,1.90,4.52),(-.75,2.25,5.03))]
for idx,(a,b) in enumerate(limb_specs):
    curve_branch('Twig_%02d'%idx,[a,tuple(Vector(a).lerp(Vector(b),.55)+Vector((0,0,.20))),b],[.08,.045,.008])
    anchors.append(Vector(b))
for i in range(14):
    a=i*2.399; z=4.20+(i%4)*.43
    end=Vector((math.cos(a)*(2.0+rng.uniform(-.2,.5))-.15,math.sin(a)*(1.6+rng.uniform(-.15,.35)),z+rng.uniform(-.15,.25)))
    start=Vector((0,0,2.8+rng.uniform(-.1,.7))); mid=start.lerp(end,.57)+Vector((0,0,.30))
    curve_branch('CrownBranch_%02d'%i,[tuple(start),tuple(mid),tuple(end)],[.15,.075,.009]); anchors.append(end)

# Convert wood and fuse intersections for organic junctions.
bpy.ops.object.select_all(action='DESELECT')
for o in wood_parts:o.select_set(True)
bpy.context.view_layer.objects.active=wood_parts[0]
bpy.ops.object.convert(target='MESH'); bpy.ops.object.join(); trunk=bpy.context.object; trunk.name='Tree02_LOD0_Trunk'
rem=trunk.modifiers.new('Organic junctions','REMESH'); rem.mode='VOXEL'; rem.voxel_size=.045
bpy.context.view_layer.objects.active=trunk; bpy.ops.object.modifier_apply(modifier=rem.name)
sm=trunk.modifiers.new('Soft handmade transitions','SMOOTH'); sm.factor=.32; sm.iterations=3; bpy.ops.object.modifier_apply(modifier=sm.name)
for p in trunk.data.polygons:p.use_smooth=True
bpy.context.view_layer.objects.active=trunk; bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.uv.smart_project(island_margin=.008); bpy.ops.object.mode_set(mode='OBJECT')

# Leaf mesh: cupped six-point leaves grouped in broad overlapping crown masses.
lv=[]; lf=[]; lm=[]
cluster_centers=[]
for a in anchors:
    cluster_centers.append((a, rng.uniform(.78,1.08),rng.uniform(.68,.95),rng.uniform(.58,.90)))
for z,rad,count in [(4.35,1.75,9),(5.05,1.75,10),(5.65,1.28,7),(6.05,.62,4)]:
    for i in range(count):
        ang=i*math.tau/count+z*.7; cluster_centers.append((Vector((math.cos(ang)*rad-.18,math.sin(ang)*rad*.78,z+rng.uniform(-.16,.18))),.92,.82,.74))

def add_leaf(pos,normal,length,width,shade):
    normal=normal.normalized(); u=normal.cross(Vector((0,0,1)))
    if u.length<.1:u=normal.cross(Vector((0,1,0)))
    u.normalize(); v=normal.cross(u).normalized(); ang=rng.uniform(0,math.tau); u,v=u*math.cos(ang)+v*math.sin(ang),-u*math.sin(ang)+v*math.cos(ang)
    base=len(lv); tip=pos+v*length*.58; stem=pos-v*length*.42
    lv.extend([tuple(stem),tuple(pos-u*width*.72-v*length*.12),tuple(pos-u*width),tuple(tip+normal*.035),tuple(pos+u*width),tuple(pos+u*width*.72-v*length*.12),tuple(pos+normal*.055)])
    lf.extend([(base,base+1,base+6),(base+1,base+2,base+6),(base+2,base+3,base+6),(base+3,base+4,base+6),(base+4,base+5,base+6),(base+5,base,base+6)]); lm.extend([shade]*6)

for center,rx,ry,rz in cluster_centers:
    for k in range(92):
        d=Vector((rng.gauss(0,1),rng.gauss(0,1),rng.gauss(0,1))).normalized(); radius=rng.random()**.42
        pos=center+Vector((d.x*rx,d.y*ry,d.z*rz))*radius
        normal=Vector((d.x*.55,d.y*.55,.35+abs(d.z)*.65+rng.uniform(-.1,.2)))
        length=rng.uniform(.105,.18); add_leaf(pos,normal,length,length*rng.uniform(.42,.60),rng.choices(range(6),weights=[1,3,4,3,2,1])[0])

me=bpy.data.meshes.new('Tree02_CanopyMesh'); me.from_pydata(lv,[],lf); me.update(); canopy=bpy.data.objects.new('Tree02_LOD0_Canopy',me); bpy.context.collection.objects.link(canopy)
for m in LEAVES:me.materials.append(m)
for p,idx in zip(me.polygons,lm):p.material_index=idx; p.use_smooth=False
attr=me.color_attributes.new(name='WindWeight',type='FLOAT_COLOR',domain='POINT')
for vert,item in zip(me.vertices,attr.data):item.color=(max(0,min(1,(vert.co.z-2.0)/4.2)),0,0,1)

# Add reusable prop models as collection instances, preserving them as separate assets.
def link_prop(path, source_name, instance_name, location, rotation=(0,0,0), scale=(1,1,1)):
    with bpy.data.libraries.load(path,link=False) as (src,dst):
        dst.objects=[source_name] if source_name in src.objects else [n for n in src.objects if n.startswith('SM_')][:1]
    ob=dst.objects[0]; ob.name=instance_name; bpy.context.collection.objects.link(ob); ob.location=location; ob.rotation_euler=rotation; ob.scale=scale; return ob

props_dir=os.path.abspath(os.path.join(OUT,'..','..','Props'))
bird=link_prop(os.path.join(props_dir,'Birdhouse_01.blend'),'SM_Birdhouse_01','Tree02_Attachment_Birdhouse',(1.00,-.58,2.32),(0,0,0),(.95,.95,.95))
lantern=link_prop(os.path.join(props_dir,'Lantern_01.blend'),'SM_Lantern_01','Tree02_Attachment_Lantern',(-2.02,-.38,2.78),(0,0,0),(.92,.92,.92))
# Warm up the imported color-only materials without changing source files.
for slot in bird.material_slots:
    if slot.material and 'roof' in slot.material.name.lower(): slot.material=ROOF
    elif slot.material: slot.material=WOOD
for slot in lantern.material_slots:
    if slot.material and ('glass' in slot.material.name.lower() or 'amber' in slot.material.name.lower()):slot.material=GLASS
    elif slot.material:slot.material=IRON

# Hanging cord and branch-side mount remain separate objects.
def cylinder_between(name,a,b,radius,material,verts=10):
    a,b=Vector(a),Vector(b); mid=(a+b)*.5
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=radius,depth=(b-a).length,location=mid)
    o=bpy.context.object;o.name=name;o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();o.data.materials.append(material);return o
cylinder_between('Tree02_Lantern_Cord',(-2.02,-.38,3.32),(-2.02,-.38,3.78),.016,IRON,10)
cylinder_between('Tree02_Birdhouse_Mount',(1.0,-.34,1.96),(1.0,-.34,2.75),.045,WOOD,12)

# Decorative hollow knot adds a readable focal point at strategy distance.
bpy.ops.mesh.primitive_torus_add(major_radius=.16,minor_radius=.045,major_segments=24,minor_segments=8,location=(.12,-.57,1.18),rotation=(math.pi/2,0,0)); knot=bpy.context.object;knot.name='Tree02_OldKnot_Rim';knot.scale=(.82,1,1.24);knot.data.materials.append(BARK)
bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=10,location=(.12,-.585,1.18)); recess=bpy.context.object;recess.name='Tree02_OldKnot_Recess';recess.scale=(.115,.025,.17);recess.data.materials.append(DARK)

# LOD copies in hidden collection: geometry reductions are non-destructive.
lod_col=bpy.data.collections.new('UNITY_LODS'); bpy.context.scene.collection.children.link(lod_col)
def lod_copy(src,name,ratio):
    o=src.copy();o.data=src.data.copy();o.name=name;lod_col.objects.link(o)
    dec=o.modifiers.new('LOD reduction','DECIMATE');dec.ratio=ratio
    bpy.context.view_layer.objects.active=o; bpy.ops.object.modifier_apply(modifier=dec.name);o.hide_render=True;o.hide_viewport=True;return o
lod_copy(trunk,'Tree02_LOD1_Trunk',.55);lod_copy(trunk,'Tree02_LOD2_Trunk',.24)
lod_copy(canopy,'Tree02_LOD1_Canopy',.58);lod_copy(canopy,'Tree02_LOD2_Canopy',.24)

# Export each LOD pair for Unity; attachments remain independent source assets.
for level in range(3):
    objs=[bpy.data.objects.get(f'Tree02_LOD{level}_Trunk'),bpy.data.objects.get(f'Tree02_LOD{level}_Canopy')]
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:o.hide_viewport=False;o.select_set(True)
    bpy.context.view_layer.objects.active=objs[0]
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUT,f'Tree_02_LOD{level}.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',apply_unit_scale=True,mesh_smooth_type='FACE',bake_anim=False)
    for o in objs:
        if level:o.hide_viewport=True

# Presentation scene.
bpy.ops.mesh.primitive_plane_add(size=60,location=(0,0,-.015));ground=bpy.context.object;ground.name='PREVIEW_ONLY_Ground';ground.data.materials.append(GROUND)
scene=bpy.context.scene;scene.render.engine='BLENDER_EEVEE_NEXT';scene.render.resolution_x=1400;scene.render.resolution_y=1400;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.62,.72,.86,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.32
for pos,energy,size,color in [((-5,-7,11),1800,5.5,(1.0,.76,.52)),((5,2,8),1050,4,(.72,.84,1.0)),((-1,5,4),650,3,(.55,.70,1.0))]:
    bpy.ops.object.light_add(type='AREA',location=pos);o=bpy.context.object;o.data.energy=energy;o.data.shape='DISK';o.data.size=size;o.data.color=color;o.rotation_euler=(Vector((0,0,3))-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.light_add(type='POINT',location=(-2.02,-.62,2.78));pl=bpy.context.object;pl.data.energy=55;pl.data.color=(1.0,.32,.06);pl.data.shadow_soft_size=.45
bpy.ops.object.camera_add();cam=bpy.context.object;scene.camera=cam;cam.data.type='ORTHO';cam.data.lens=55
scene.view_settings.look='AgX - Medium High Contrast'

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'Tree_02_Master.blend'))
views=[('hero',(8.8,-15.5,8.0),(-.1,0,3.0),9.7),('detail',(4.0,-9.5,4.4),(0,-.05,2.2),5.2),('reverse',(-10,12,7.2),(0,0,3.1),9.8)]
for label,pos,target,scale in views:
    cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
    scene.render.filepath=os.path.join(OUT,f'Tree_02_{label}.png');bpy.ops.render.render(write_still=True)

print('TREE02_DONE','leaves',len(lf)//6,'wood_faces',len(trunk.data.polygons),'canopy_faces',len(canopy.data.polygons))
