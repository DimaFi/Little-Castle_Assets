"""Deterministic stylized broadleaf tree. Units: meters. Seed changes one asset.
Geometry leaves require no opacity textures; vertex colors carry wind weights.
"""
import bpy, math, random, os, json
from mathutils import Vector
OUT=os.path.dirname(os.path.abspath(__file__))
SEED=28
r=random.Random(SEED)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
def material(name,col):
    m=bpy.data.materials.new(name); m.diffuse_color=(*col,1); m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF'); p.inputs['Base Color'].default_value=(*col,1); p.inputs['Roughness'].default_value=.87
    return m
bark=[material('Oak bark '+str(i),(.20+i*.018,.115+i*.012,.058+i*.008)) for i in range(4)]
greens=[material('Leaf '+str(i),c) for i,c in enumerate([(.09,.19,.018),(.16,.28,.028),(.23,.34,.05),(.30,.38,.075),(.13,.25,.035),(.36,.42,.10)])]
for m in greens:
    p=m.node_tree.nodes.get('Principled BSDF'); p.inputs['Subsurface Weight'].default_value=.02; p.inputs['Specular IOR Level'].default_value=.15
verts=[]; faces=[]; mids=[]
def branch(points,radii,sides=10):
    base=len(verts); pts=[Vector(p) for p in points]
    for i,(p,rad) in enumerate(zip(pts,radii)):
        tangent=(pts[min(i+1,len(pts)-1)]-pts[max(0,i-1)]).normalized(); u=tangent.cross(Vector((0,1,0))).normalized(); v=tangent.cross(u).normalized()
        for j in range(sides):
            a=j*math.tau/sides; rr=rad*(1+.10*math.sin(j*3.1+i*.5)); verts.append(tuple(p+rr*(u*math.cos(a)+v*math.sin(a))))
    faces.append(tuple(base+j for j in reversed(range(sides)))); mids.append(0)
    for i in range(len(pts)-1):
        for j in range(sides): faces.append((base+i*sides+j,base+i*sides+(j+1)%sides,base+(i+1)*sides+(j+1)%sides,base+(i+1)*sides+j)); mids.append(j%4)
    faces.append(tuple(base+(len(pts)-1)*sides+j for j in range(sides))); mids.append(0)
branch([(0,0,0),(.08,0,.32),(-.08,.02,1.0),(-.14,.03,1.8),(.12,.03,2.55),(.32,.13,3.2),(.21,.18,4.2),(.32,.12,5.45)],[.56,.46,.36,.32,.27,.20,.12,.025],14)
for i in range(7):
    a=i*math.tau/7+.2; branch([(math.cos(a)*1.02,math.sin(a)*.9,.025),(math.cos(a)*.55,math.sin(a)*.49,.13),(.02,0,.47)],[.035,.14,.25],8)
clusters=[]
for i in range(11):
    a=i*2.399; height=2.0+(i%4)*.40; reach=2.1+r.random()*.70
    origin=Vector((.05,0,height)); mid=Vector((math.cos(a)*reach*.52,math.sin(a)*reach*.52,height+.60)); end=Vector((math.cos(a)*reach,math.sin(a)*reach,3.65+(i%4)*.38))
    branch([origin,mid*.65+origin*.35,mid,end],[.18,.14,.105,.025])
    for j in range(4):
        aa=a+(j-1.5)*.43; tip=end+Vector((math.cos(aa)*r.uniform(.10,.60),math.sin(aa)*r.uniform(.10,.60),r.uniform(.15,.85)))
        start=mid.lerp(end,.48+j*.10); branch([start,start.lerp(tip,.55)+Vector((0,0,.15)),tip],[.065,.036,.008],7)
        clusters.append((tip,r.uniform(.65,.90),r.uniform(.57,.78),r.uniform(.60,.90)))
for i in range(9):
    a=i*2.399; p=Vector((math.cos(a)*r.uniform(.25,1.2),math.sin(a)*r.uniform(.25,1.2),5.1+r.uniform(-.1,.55)))
    branch([(.2,.15,3.9),tuple(p)],[.08,.012],7); clusters.append((p,.90,.85,.78))
clusters.append((Vector((1.30,-.3,5.10)),1.05,.95,.90))
clusters.append((Vector((-.7,.45,5.55)),1.05,.95,.80))
def mesh_obj(name,v,f,materials,indices):
    me=bpy.data.meshes.new(name); me.from_pydata(v,[],f); me.update(); ob=bpy.data.objects.new(name,me); bpy.context.collection.objects.link(ob)
    for m in materials: me.materials.append(m)
    for p,mi in zip(me.polygons,indices): p.material_index=mi; p.use_smooth=True
    return ob
trunk=mesh_obj('SM_Tree01_Wood',verts,faces,bark,mids)
lv=[]; lf=[]; lm=[]
for center,rx,ry,rz in clusters:
    for k in range(185):
        # Volume clusters with irregular lobed outline, not solid green spheres.
        d=Vector((r.gauss(0,1),r.gauss(0,1),r.gauss(0,1))).normalized(); rad=r.random()**(.36)
        p=center+Vector((d.x*rx,d.y*ry,d.z*rz))*rad
        normal=Vector((d.x*.5+r.uniform(-.5,.5),d.y*.5+r.uniform(-.5,.5),r.uniform(.20,1))).normalized()
        u=normal.cross(Vector((0,1,0))).normalized(); v=normal.cross(u)
        ang=r.uniform(0,math.tau); u,v=u*math.cos(ang)+v*math.sin(ang),-u*math.sin(ang)+v*math.cos(ang)
        length=r.uniform(.09,.16); width=length*r.uniform(.48,.70); base=len(lv)
        lv.append(tuple(p+normal*.012))
        for j in range(8):
            a=math.tau*j/8; lv.append(tuple(p+u*(math.cos(a)*length)+v*(math.sin(a)*width)))
        shade=r.choices(range(6),weights=[1,2,3,2,2,1])[0]
        for j in range(8): lf.append((base,base+1+j,base+1+(j+1)%8)); lm.append(shade)
canopy=mesh_obj('SM_Tree01_Canopy',lv,lf,greens,lm)
# Colors are stable placement metadata: R=height wind mask; G/B reserved.
for ob in [trunk,canopy]:
    attr=ob.data.color_attributes.new(name='WindWeight',type='FLOAT_COLOR',domain='POINT')
    for vert,item in zip(ob.data.vertices,attr.data): item.color=(max(0,min(1,(vert.co.z-.6)/5.5)),0,0,1)
    bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True); bpy.context.view_layer.objects.active=ob
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.normals_make_consistent(inside=False); bpy.ops.uv.smart_project(island_margin=.005); bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.select_all(action='DESELECT'); trunk.select_set(True); canopy.select_set(True); bpy.context.view_layer.objects.active=trunk
bpy.ops.export_scene.fbx(filepath=os.path.join(OUT,'Tree_01.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Y',axis_up='Z',apply_unit_scale=True,mesh_smooth_type='FACE',bake_anim=False)
scene=bpy.context.scene
scene.world.use_nodes=True; scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.69,.78,.9,1); scene.world.node_tree.nodes['Background'].inputs[1].default_value=.45
groundmat=material('Preview ground',(.30,.34,.22)); bpy.ops.mesh.primitive_plane_add(size=200); ground=bpy.context.object; ground.name='PREVIEW_ONLY_Ground'; ground.data.materials.append(groundmat)
bpy.ops.object.light_add(type='AREA',location=(-4,-6,10)); light=bpy.context.object; light.data.energy=2200; light.data.size=5; light.rotation_euler=(Vector((0,0,3))-light.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.light_add(type='AREA',location=(3,4,9)); light=bpy.context.object; light.data.energy=1400; light.data.size=4; light.rotation_euler=(Vector((0,0,3))-light.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(10,-14,9)); camera=bpy.context.object; scene.camera=camera; camera.data.type='ORTHO'; camera.data.ortho_scale=10.6; camera.rotation_euler=(Vector((0,0,3))-camera.location).to_track_quat('-Z','Y').to_euler()
scene.render.engine='CYCLES'; scene.cycles.samples=32; scene.cycles.use_denoising=True; scene.render.resolution_x=1200; scene.render.resolution_y=1200; scene.render.resolution_percentage=100; scene.view_settings.view_transform='AgX'
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'Tree_01.blend'))
for name,pos in [('hero',(10,-14,9)),('reverse',(-11,10,8))]:
    camera.location=pos; camera.rotation_euler=(Vector((0,0,3))-camera.location).to_track_quat('-Z','Y').to_euler(); scene.render.filepath=os.path.join(OUT,'Tree_01_'+name+'.png'); bpy.ops.render.render(write_still=True)
print('TREE_DONE seed',SEED,'leaves',len(lv)//9,'triangles leaves',len(lf))
