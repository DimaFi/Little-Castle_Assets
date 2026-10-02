"""Cozy oak kit. Blender 4.4; metres; hand-directed forms, deterministic seed.
Run: blender -b --factory-startup --python build_oak_kit.py -- --stage wood|canopy|final
Previous assets and project maps are never modified.
"""
import bpy, bmesh, math, random, os, sys, json
import numpy as np
from mathutils import Vector, Matrix

ROOT=os.path.dirname(os.path.abspath(__file__))
PROJECT=os.path.abspath(os.path.join(ROOT,'../../..'))
MAT=os.path.join(PROJECT,'Mat')
for sub in ['Textures','Exports','Renders','QA']: os.makedirs(os.path.join(ROOT,sub),exist_ok=True)
STAGE=sys.argv[sys.argv.index('--stage')+1] if '--stage' in sys.argv else 'final'
r=random.Random(7319)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene
scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1

def collection(name,parent=None):
    c=bpy.data.collections.new(name);(parent or scene.collection).children.link(c);return c
tree=collection('Tree');source=collection('SOURCE • editable growth structure')
trunk_col=collection('Trunk',source);root_col=collection('Roots',source)
main_col=collection('MainBranches',source);secondary_col=collection('SecondaryBranches',source)
leaf_col=collection('LeafClusters',tree);ground_col=collection('GroundDecoration')
library=collection('MODULE_LIBRARY');exports=collection('GAME_EXPORT');studio=collection('STUDIO')

def put(o,c):
    for co in list(o.users_collection):co.objects.unlink(o)
    c.objects.link(o);return o
def active(o):
    bpy.ops.object.select_all(action='DESELECT');o.hide_set(False);o.select_set(True);bpy.context.view_layer.objects.active=o
def mesh(name,verts,faces,materials,col,uvs=None,mids=None):
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update()
    o=bpy.data.objects.new(name,me);col.objects.link(o)
    for m in materials:me.materials.append(m)
    for p in me.polygons:p.use_smooth=True;p.material_index=mids[p.index] if mids else 0
    if uvs:
        layer=me.uv_layers.new(name='UV0')
        for p in me.polygons:
            for li in p.loop_indices:layer.data[li].uv=uvs[me.loops[li].vertex_index]
    return o
def material(name,color,rough=.82):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Roughness'].default_value=rough;p.inputs['Specular IOR Level'].default_value=.22
    return m
def texture(m,path,noncolor=False):
    im=bpy.data.images.load(path,check_existing=True)
    im.colorspace_settings.name='Non-Color' if noncolor else 'sRGB'
    n=m.node_tree.nodes.new('ShaderNodeTexImage');n.image=im;return n

# Low-frequency analytic bark maps: no photo noise or displacement tessellation.
# Four broad wandering grooves per tile; V is always the growth direction.
def bark_maps():
    N=512;v,u=np.mgrid[0:N,0:N].astype(float)/N
    phase=2*math.pi*(4*u+.105*np.sin(2*math.pi*v)+.035*np.sin(4*math.pi*v+2*math.pi*u))
    ridge=(.5+.5*np.cos(phase))**.42
    h=.20+.63*ridge+.05*np.sin(2*math.pi*u+2*math.pi*v)
    # Long, sparse grooves split plates without fine cracks.
    h-=.09*((.5+.5*np.cos(phase*2+.8))**18)*(.5+.5*np.sin(2*math.pi*v))**4
    dx=(np.roll(h,-1,1)-np.roll(h,1,1))*4
    dy=(np.roll(h,-1,0)-np.roll(h,1,0))*4
    normal=np.stack([-dx,-dy,np.ones_like(h)],-1);normal/=np.linalg.norm(normal,axis=-1)[...,None]
    warm=np.array([.46,.275,.125]);light=np.array([.61,.405,.205])
    color=warm+(light-warm)*ridge[...,None]
    values={'BaseColor':color,'Normal':normal*.5+.5,'Height':h,'Roughness':.78+.12*(1-ridge),'AO':.83+.17*ridge}
    for label,a in values.items():
        path=os.path.join(ROOT,'Textures','T_Oak_Bark_A_'+label+'.png')
        if os.path.exists(path):continue
        rgba=np.ones((N,N,4),dtype=np.float32)
        rgba[:,:,:3]=a[...,None] if a.ndim==2 else a
        im=bpy.data.images.new('T_Oak_Bark_A_'+label,width=N,height=N,alpha=False)
        im.colorspace_settings.name='sRGB' if label=='BaseColor' else 'Non-Color'
        im.pixels.foreach_set(rgba.ravel());im.filepath_raw=path;im.file_format='PNG';im.save()
bark_maps()
bark=material('M_Oak_Bark',(.45,.27,.13));n=bark.node_tree.nodes;l=bark.node_tree.links;p=n.get('Principled BSDF')
for label,sock in [('BaseColor','Base Color'),('Roughness','Roughness')]:
    t=texture(bark,os.path.join(ROOT,'Textures','T_Oak_Bark_A_'+label+'.png'),label!='BaseColor');l.new(t.outputs['Color'],p.inputs[sock])
t=texture(bark,os.path.join(ROOT,'Textures','T_Oak_Bark_A_Normal.png'),True)
nm=n.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.8;l.new(t.outputs['Color'],nm.inputs['Color']);l.new(nm.outputs['Normal'],p.inputs['Normal'])
# Blend the existing painted Bark set at low contrast, after evaluating it in project.
# Logs_Bark is photographic; Bark is hand-painted and useful at a coarser scale.
paint=texture(bark,os.path.join(MAT,'Bark','Bark_BaseColor.png'))
coord=n.new('ShaderNodeVectorMath');coord.operation='MULTIPLY';coord.inputs[1].default_value=(.4,.45,1)
tc=n.new('ShaderNodeTexCoord');l.new(tc.outputs['UV'],coord.inputs[0]);l.new(coord.outputs[0],paint.inputs['Vector'])
base=p.inputs['Base Color'].links[0].from_socket
mix=n.new('ShaderNodeMixRGB');mix.blend_type='MIX';mix.inputs[0].default_value=.70;l.new(base,mix.inputs[1]);l.new(paint.outputs['Color'],mix.inputs[2]);l.new(mix.outputs[0],p.inputs['Base Color'])
pn=texture(bark,os.path.join(MAT,'Bark','Bark_Normal.png'),True);l.new(coord.outputs[0],pn.inputs['Vector'])
nm.inputs['Strength'].default_value=.28;l.new(pn.outputs['Color'],nm.inputs['Color'])

leaf=material('M_Oak_Foliage',(.24,.33,.065));n=leaf.node_tree.nodes;l=leaf.node_tree.links;p=n.get('Principled BSDF')
t=texture(leaf,os.path.join(MAT,'T_Foliage','T_Foliage_BaseColor.png'))
l.new(t.outputs['Color'],p.inputs['Base Color']);l.new(t.outputs['Alpha'],p.inputs['Alpha'])
mix=n.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1;mix.inputs[2].default_value=(.56,.67,.40,1)
l.new(t.outputs['Color'],mix.inputs[1]);l.new(mix.outputs[0],p.inputs['Base Color'])
p.inputs['Subsurface Weight'].default_value=0;p.inputs['Specular IOR Level'].default_value=.10
leaf.surface_render_method='DITHERED';leaf.use_backface_culling=False
leaf.use_transparency_overlap=False
green=[material('M_Plant_'+str(i),c) for i,c in enumerate([(.13,.21,.035),(.24,.32,.055),(.37,.42,.08)])]
stone_mats=[material('M_Stone_'+str(i),c) for i,c in enumerate([(.41,.385,.32),(.49,.46,.39),(.35,.34,.30)])]
moss=material('M_Moss',(.21,.27,.065));soil=material('M_Soil',(.29,.18,.085))
cream=material('M_Petal_Cream',(.85,.79,.57));gold=material('M_Pollen',(.7,.40,.055))
purple=material('M_Petal_Lavender',(.34,.19,.49));dark=material('M_Knot_Interior',(.05,.022,.009))

def interpolate(points,radii,steps=4):
    ps=[Vector(p) for p in points];out=[];rr=[]
    for i in range(len(ps)-1):
        p0=ps[max(0,i-1)];p1=ps[i];p2=ps[i+1];p3=ps[min(len(ps)-1,i+2)]
        for k in range(steps):
            t=k/steps
            out.append(.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t*t*t))
            rr.append(radii[i]*(1-t)+radii[i+1]*t)
    out.append(ps[-1]);rr.append(radii[-1]);return out,rr

paths=[]
def tube(name,points,radii,col,sides=16,steps=4,record=True,mat=bark):
    ps,rr=interpolate(points,radii,steps);verts=[];faces=[];uv=[];length=0;frames=[]
    previous=None
    for i,(c,rad) in enumerate(zip(ps,rr)):
        axis=(ps[min(i+1,len(ps)-1)]-ps[max(0,i-1)]).normalized()
        if previous is None:
            reference=Vector((0,1,0)) if abs(axis.y)<.9 else Vector((1,0,0))
            side=axis.cross(reference).normalized()
        else:side=(previous-axis*previous.dot(axis)).normalized()
        other=axis.cross(side).normalized();previous=side;frames.append((side,other))
        if i:length+=(c-ps[i-1]).length
        for j in range(sides+1):
            a=j*math.tau/sides
            ridge=1+.045*math.sin(7*a+length*.7)+.026*math.sin(11*a-length*.45)
            verts.append(tuple(c+rad*ridge*(side*math.cos(a)+other*math.sin(a))))
            uv.append((j/sides*math.tau*rad/1.4,length/1.4))
    for i in range(len(ps)-1):
        for j in range(sides):a=i*(sides+1)+j;faces.append((a,a+1,a+sides+2,a+sides+1))
    faces.extend([tuple(reversed(range(sides))),tuple((len(ps)-1)*(sides+1)+j for j in range(sides))])
    o=mesh(name,verts,faces,[mat],col,uv)
    # Weld UV seam without destroying per-loop UV coordinates.
    bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00001);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
    o['growth_path']=[list(p) for p in ps];o['growth_radii']=rr
    if record:paths.append((ps,rr,frames,name))
    return o

trunk_points=[(0,0,-.16),(-.17,.015,.7),(-.06,.07,1.5),(.26,.05,2.32),(.14,.09,3.14),(-.22,.18,4.05),(-.35,.23,4.9),(-.12,.25,5.72)]
trunk_radii=[.73,.64,.52,.48,.37,.27,.15,.025]
wood_parts=[tube('Trunk',trunk_points,trunk_radii,trunk_col,sides=24)]
# Seven unequal buttresses sweep down to grade. Each starts inside the trunk.
root_specs=[(-2.85,1.7,.37),(-1.97,1.5,.39),(-1.10,1.86,.41),(-.18,1.42,.34),(.77,1.55,.32),(1.65,1.75,.37),(2.47,1.34,.30)]
for i,(a,reach,width) in enumerate(root_specs):
    def rp(rad,z,da=0):return (math.cos(a+da)*rad,math.sin(a+da)*rad,z)
    pts=[rp(.15,.72),rp(.53,.38),rp(reach*.67,.13,.09),rp(reach,-.055,.17)]
    wood_parts.append(tube('Root_%02d'%i,pts,[width,width*.85,width*.44,.015],root_col))

primary=[
 ([(.06,.05,2.00),(.79,.06,2.84),(1.22,.13,3.9),(.91,.24,5.68)],[.43,.36,.22,.026]),
 ([(-.03,.05,2.29),(-.91,-.08,3.02),(-1.76,-.07,3.73),(-2.06,-.03,4.51)],[.37,.29,.17,.026]),
 ([(.24,.06,2.53),(1.13,-.15,3.05),(1.89,-.28,3.76),(2.28,-.23,4.66)],[.35,.26,.15,.021]),
 ([(.14,.11,2.67),(.15,.80,3.22),(-.29,1.48,4.20),(-.55,1.60,5.04)],[.30,.23,.14,.02]),
 ([(-.08,.1,3.44),(-.63,-.65,3.84),(-.92,-1.24,4.45),(-.78,-1.37,5.22)],[.24,.19,.10,.018]),
 ([(.28,.08,3.01),(.82,.67,3.76),(1.45,1.15,4.57),(1.35,1.14,5.39)],[.27,.21,.12,.02]),
 ([(-.2,.14,3.61),(-.88,.66,4.17),(-1.34,1.02,4.96),(-1.15,.91,5.80)],[.23,.18,.09,.016])]
for i,(pts,rr) in enumerate(primary):wood_parts.append(tube('Primary_%02d'%i,pts,rr,main_col,sides=18))
secondary=[
 ([(-1.5,-.06,3.5),(-1.94,-.64,4.04),(-2.08,-.83,4.73)],[.14,.085,.015]),
 ([(-.95,-.08,3.05),(-1.21,.48,3.66),(-1.49,.68,4.40)],[.17,.10,.016]),
 ([(1.6,-.23,3.52),(1.62,-1.03,4.14),(1.44,-1.28,4.91)],[.14,.08,.015]),
 ([(.95,.1,3.18),(1.77,.38,4.08),(2.18,.68,4.97)],[.16,.09,.015]),
 ([(-.19,.18,4.0),(-.78,-.16,4.83),(-.57,-.23,5.99)],[.19,.10,.018]),
 ([(.03,1.07,3.65),(.51,1.73,4.48),(.34,1.81,5.17)],[.14,.08,.013]),
 ([(-.84,-1.13,4.22),(-.03,-1.57,4.70),(.26,-1.45,5.3)],[.11,.06,.012]),
 ([(1.16,1.0,4.18),(1.90,1.19,4.62),(2.08,1.09,5.2)],[.11,.06,.012])]
for i,(pts,rr) in enumerate(secondary):wood_parts.append(tube('Secondary_%02d'%i,pts,rr,secondary_col,sides=12))

def copy_join(obs,name,col):
    bpy.context.view_layer.update()
    copies=[]
    for ob in obs:
        c=ob.copy();c.data=ob.data.copy();col.objects.link(c);c.matrix_world=ob.matrix_world.copy();c.hide_render=False;c.hide_viewport=False;c.hide_set(False)
        if c.data.uv_layers:c.data.uv_layers[0].name='UV0'
        copies.append(c)
    active(copies[0])
    for c in copies:c.select_set(True)
    bpy.ops.object.join();o=bpy.context.object;o.name=name
    scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR');bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
    return o
def simplify(o,ratio):
    active(o);d=o.modifiers.new('Silhouette-preserving reduction','DECIMATE');d.ratio=ratio;bpy.ops.object.modifier_apply(modifier=d.name)
    o.data.validate();o.data.update()
def union(obs,name,col,voxel=.055,budget=7500):
    o=copy_join(obs,name,col);active(o)
    mod=o.modifiers.new('Continuous branch crotches and root transitions','REMESH');mod.mode='VOXEL';mod.voxel_size=voxel;bpy.ops.object.modifier_apply(modifier=mod.name)
    mod=o.modifiers.new('Hand softened forms','SMOOTH');mod.factor=.62;mod.iterations=4;bpy.ops.object.modifier_apply(modifier=mod.name)
    o.data.calc_loop_triangles();simplify(o,min(1,budget/len(o.data.loop_triangles)))
    # Voxel sampling may leave tiny detached tip shells. Keep the continuous wood.
    bm=bmesh.new();bm.from_mesh(o.data);pending=set(bm.verts);components=[]
    while pending:
        stack=[pending.pop()];component=[]
        while stack:
            v=stack.pop();component.append(v)
            for edge in v.link_edges:
                other=edge.other_vert(v)
                if other in pending:pending.remove(other);stack.append(other)
        components.append(component)
    if len(components)>1:
        largest=max(components,key=len)
        bmesh.ops.delete(bm,geom=[v for c in components if c is not largest for v in c],context='VERTS')
    bm.to_mesh(o.data);bm.free();o.data.update()
    for p in o.data.polygons:p.use_smooth=True
    return o

def flow_uv(o,field_paths):
    # Assign a single branch frame per face; along-grain V and world-sized U.
    segments=[]
    for ps,rr,frames,name in field_paths:
        dist=0
        for i in range(len(ps)-1):
            vec=ps[i+1]-ps[i];length=vec.length
            segments.append((ps[i],vec/length,length,rr[i],rr[i+1],frames[i],dist,name,max(1,round(math.tau*max(rr)/1.4))));dist+=length
    starts=np.array([list(s[0]) for s in segments]);axes=np.array([list(s[1]) for s in segments]);lengths=np.array([s[2] for s in segments]);r0=np.array([s[3] for s in segments]);r1=np.array([s[4] for s in segments])
    uv=o.data.uv_layers.get('UV0') or o.data.uv_layers.new(name='UV0')
    for face in o.data.polygons:
        center=sum((o.data.vertices[i].co for i in face.vertices),Vector())/len(face.vertices)
        q=np.array(center)-starts;raw=np.sum(q*axes,axis=1);t=np.clip(raw,0,lengths);d=np.linalg.norm(q-axes*t[:,None],axis=1)
        rad=r0+(r1-r0)*t/lengths
        idx=int(np.argmin(d/(rad+.035)+np.abs(raw-t)*2))
        start,axis,length,ra,rb,(side,other),dist,name,repeats=segments[idx];coords=[]
        for li in face.loop_indices:
            q=o.data.vertices[o.data.loops[li].vertex_index].co-start
            longitudinal=q.dot(axis);a=math.atan2(q.dot(other),q.dot(side));radius=ra+(rb-ra)*max(0,min(1,longitudinal/length))
            coords.append((li,a,radius,longitudinal))
        seam=max(x[1] for x in coords)-min(x[1] for x in coords)>math.pi
        for li,a,rad,z in coords:
            if seam and a<0:a+=math.tau
            uv.data[li].uv=(a/math.tau*repeats,(dist+z)/1.4)
    o.data.uv_layers.active=uv;uv.active_render=True
    for layer in list(o.data.uv_layers):
        if layer.name!=uv.name:o.data.uv_layers.remove(layer)

wood=union(wood_parts,'Oak_ContinuousWood',tree,budget=8500)
flow_uv(wood,paths)
source.hide_render=True;source.hide_viewport=True

# A shallow actual hollow, with an uneven lip growing out of the grain.
bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=12,location=(.05,-.46,1.50))
cutter=bpy.context.object;cutter.scale=(.17,.26,.225);active(cutter);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
active(wood);mod=wood.modifiers.new('Shallow old branch hollow','BOOLEAN');mod.operation='DIFFERENCE';mod.object=cutter
bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cutter,do_unlink=True)
flow_uv(wood,paths)
bpy.ops.mesh.primitive_torus_add(major_segments=28,minor_segments=7,location=(.05,-.483,1.50),rotation=(math.pi/2,.05,-.12),major_radius=.184,minor_radius=.041)
rim=put(bpy.context.object,tree);rim.name='Knot_Rim';rim.scale=(.90,1.19,.70);rim.data.materials.append(bark)
active(rim);bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
for p in rim.data.polygons:p.use_smooth=True

def setup_studio():
    floor=material('Studio_Sand',(.58,.54,.46),.9)
    bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,0));o=put(bpy.context.object,studio);o.name='Studio_Ground';o.data.materials.append(floor)
    world=bpy.data.worlds.new('Warm studio');scene.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.72,.78,.88,1);world.node_tree.nodes['Background'].inputs[1].default_value=.4
    for name,pos,power,size,color in [('Key',(-3,-4,10),1600,5,(1,.88,.69)),('Fill',(5,-1,7),900,5,(.80,.88,1)),('Rim',(1,5,9),1800,4,(1,.91,.68))]:
        data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size;data.color=color
        o=bpy.data.objects.new(name,data);studio.objects.link(o);o.location=pos;o.rotation_euler=(Vector((0,0,3))-o.location).to_track_quat('-Z','Y').to_euler()
    data=bpy.data.cameras.new('Camera');cam=bpy.data.objects.new('Camera',data);studio.objects.link(cam);scene.camera=cam;data.type='ORTHO'
    scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True;scene.cycles.transparent_max_bounces=16
    try:
        prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
        for device in prefs.devices:device.use=device.type=='OPTIX'
        scene.cycles.device='GPU'
    except Exception:pass
    scene.render.resolution_x=1000;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
    scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast'
    scene.render.image_settings.file_format='PNG'
def render(label,pos=(9,-16,10),target=(0,0,3.25),scale=8.8,res=1000):
    if '--skip-renders' in sys.argv:return
    cam=scene.camera;cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
    scene.render.resolution_x=res;scene.render.resolution_y=res;scene.render.filepath=os.path.join(ROOT,'Renders',label+'.png')
    bpy.ops.render.render(write_still=True);print('RENDER_DONE',label,flush=True)
setup_studio()
if STAGE=='wood':
    render('01_wood_gameplay');render('01_wood_roots',(5,-9,4),(0,0,1.55),4.5)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,'Oak_Structure.blend'));sys.exit()

# These are distinct visual masses, not a sphere scattered with random cards.
masses=[
 ('Crown',(-.22,.12,5.95),(1.03,.92,.90),(-.12,.25,5.25)),
 ('UpperLeft',(-1.10,.40,5.43),(.99,.90,.93),(-1.15,.91,5.10)),
 ('UpperRight',(1.03,.45,5.58),(.99,.87,.92),(.97,.24,4.93)),
 ('Left',(-2.01,-.03,4.24),(.87,.84,.88),(-1.80,-.07,3.86)),
 ('Right',(2.11,-.19,4.39),(.91,.87,.84),(1.99,-.25,4.02)),
 ('FrontLeft',(-1.12,-1.10,4.25),(.94,.81,.79),(-.9,-1.18,4.39)),
 ('FrontRight',(.97,-1.17,4.52),(.91,.76,.84),(1.62,-1.03,4.14)),
 ('BackLeft',(-.83,1.39,4.96),(1.01,.82,.94),(-.45,1.55,4.71)),
 ('BackRight',(1.17,1.28,4.99),(.96,.82,.87),(1.45,1.15,4.57)),
 ('FrontCrown',(.05,-.72,5.55),(.92,.76,.79),(-.1,.18,4.45))]
rects=[(14,22,452,414),(468,12,863,422),(873,28,1244,403),(22,425,439,716),(452,427,809,738),(838,413,1241,726)]

def cluster(name,center,radii,col,seed,count=35):
    rand=random.Random(seed);verts=[];faces=[];uv=[];center=Vector(center)
    # Stratified domed shell plus inner bunches. Normals turn outward and upward.
    # Nine-vertex curved patches avoid a visible crossed-plane X.
    for j in range(count):
        z=1-2*(j+.5)/count;phi=j*2.399963+seed*.13;rr=math.sqrt(max(0,1-z*z))
        d=Vector((rr*math.cos(phi),rr*math.sin(phi),z))
        rad=.70 if j%7==0 else .90
        pos=center+Vector((d.x*radii[0],d.y*radii[1],d.z*radii[2]))*rad
        normal=Vector((d.x,d.y,d.z*.74+.40)).normalized()
        right=normal.cross(Vector((0,0,1)))
        if right.length<.1:right=Vector((1,0,0))
        right.normalize();up=right.cross(normal).normalized()
        size=rand.uniform(.77,.98)*max(radii)
        x0,y0,x1,y1=rects[(j+seed)%len(rects)];base=len(verts)
        for y in range(3):
            for x in range(3):
                xx=x/2;yy=y/2
                bulge=.12*size*(1-4*(xx-.5)**2)*(1-4*(yy-.5)**2)
                verts.append(tuple(pos+right*((xx-.5)*size)+up*((yy-.5)*size)+normal*bulge))
                uv.append(((x0+xx*(x1-x0))/1254,1-(y1-yy*(y1-y0))/1254))
        for y in range(2):
            for x in range(2):a=base+y*3+x;faces.append((a,a+1,a+4,a+3))
    o=mesh(name,verts,faces,[leaf],col,uv);o['cluster_groups']=count;o['growth']='Outward/upward from supporting branch; curved whole-bunch cards'
    return o

canopy=[]
for i,(name,c,rr,anchor) in enumerate(masses):
    # User art-direction revision: generous crown, with stronger side/lower masses.
    # Keep the established wood; scale bunches themselves, not leaf count.
    side=name in {'Left','Right','FrontLeft','FrontRight','BackLeft','BackRight'}
    c=(c[0]*1.15,c[1]*1.24,c[2]+(.08 if not side else -.06))
    rr=(rr[0]*(1.27 if side else 1.18),rr[1]*1.28,rr[2]*(1.23 if side else 1.16))
    o=cluster('LeafMass_'+name,c,rr,leaf_col,40+i,count=36);o['parent_branch_attachment']=anchor;canopy.append(o)
if STAGE=='canopy':
    render('02_canopy_gameplay');render('02_canopy_front',(0,-18,5),(0,0,3.3),8.1);render('02_canopy_top',(0,0,18),(0,0,0),7.5)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,'Oak_Canopy.blend'));sys.exit()

# Modular kit and final export are defined below.
modules=[]
def register(o):
    active(o);scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR');bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
    modules.append(o);return o
def finish_module(parts,name,ratio=1):
    o=copy_join(parts,name,library)
    if ratio<1:simplify(o,ratio)
    for part in parts:bpy.data.objects.remove(part,do_unlink=True)
    return register(o)

root_module=tube('SM_TreeRoot_A',[(0,0,.21),(.5,.08,.17),(1.01,.27,.10),(1.46,.41,.01)],[.28,.22,.12,.015],library,record=False)
register(root_module)
branch_specs=[
 ('Small',[(0,0,0),(.1,.1,.40),(.35,.13,.91)],[.14,.09,.016]),
 ('Medium',[(0,0,0),(.21,.07,.61),(.47,-.05,1.05),(.79,.03,1.50)],[.22,.17,.10,.018]),
 ('Large',[(0,0,0),(.33,.04,.73),(.62,-.09,1.30),(1.02,.10,2.04)],[.31,.23,.14,.024]),
 ('Fork',[(0,0,0),(.12,.02,.6),(.42,.08,1.2),(.75,.13,1.65)],[.25,.19,.11,.018]),
 ('Curved',[(0,0,0),(-.29,.07,.51),(-.35,.04,1.04),(.01,.0,1.53),(.51,.12,1.78)],[.25,.21,.16,.10,.015])]
for idx,(label,pts,rr) in enumerate(branch_specs):
    parts=[tube('Branch_'+label,pts,rr,library,record=False)]
    if label=='Fork':parts.append(tube('Fork_side',[(.11,.02,.58),(-.32,-.03,1.06),(-.53,.08,1.56)],[.16,.10,.017],library,record=False))
    # Branch modules are complete wood geometry, with closed bases and tapered tips.
    register(parts[0]) if len(parts)==1 else None
    if len(parts)==1:parts[0].name='SM_Branch_'+label+'_A'
    else:
        localpaths=[]
        for part in parts:
            ps=[Vector(p) for p in part['growth_path']];radii=list(part['growth_radii']);frames=[]
            for i,p0 in enumerate(ps):
                axis=(ps[min(i+1,len(ps)-1)]-ps[max(0,i-1)]).normalized();u=axis.cross(Vector((0,1,0))).normalized();frames.append((u,axis.cross(u)))
            localpaths.append((ps,radii,frames,part.name))
        o=union(parts,'SM_Branch_Fork_A',library,voxel=.03,budget=1300);flow_uv(o,localpaths)
        for part in parts:bpy.data.objects.remove(part,do_unlink=True)
        register(o)

for i,(label,rr,count) in enumerate([('Small_A',(.39,.34,.30),16),('Medium_A',(.64,.54,.49),24),('Large_A',(.90,.76,.64),34),('Medium_B',(.58,.69,.44),24),('Large_B',(.84,.90,.62),34)]):
    register(cluster('SM_LeafCluster_'+label,(0,0,rr[2]*1.12),rr,library,91+i,count))

def stone(name,scale,seed,mossy=False):
    rand=random.Random(seed)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=1)
    o=put(bpy.context.object,library);o.name=name
    for vert in o.data.vertices:
        co=vert.co;factor=1+rand.uniform(-.13,.13)
        co.x*=scale[0]*factor;co.y*=scale[1]*factor;co.z*=scale[2]*factor
        co.x+=.12*co.z;co.z=max(-scale[2]*.6,co.z)
    active(o);simplify(o,.32)
    mod=o.modifiers.new('Soft chipped edges','BEVEL');mod.width=.033;mod.segments=2;bpy.ops.object.modifier_apply(modifier=mod.name)
    for m in stone_mats+([moss] if mossy else []):o.data.materials.append(m)
    for face in o.data.polygons:
        face.use_smooth=True;face.material_index=1 if face.normal.z>.72 else 0
        if mossy and face.normal.z>.35 and rand.random()<.8:face.material_index=3
    # Shift to ground; preserve rounded bevel strips but broad large planes.
    low=min(v.co.z for v in o.data.vertices)
    for v in o.data.vertices:v.co.z-=low
    mod=o.modifiers.new('Weighted broad stone planes','WEIGHTED_NORMAL');mod.keep_sharp=True;mod.weight=40;bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(island_margin=.02);bpy.ops.object.mode_set(mode='OBJECT')
    return register(o)
for i,(name,sc) in enumerate([('Small_A',(.22,.18,.19)),('Small_B',(.28,.16,.13)),('Medium_A',(.44,.33,.34)),('Medium_B',(.35,.42,.27)),('Large_A',(.65,.51,.58)),('Mossy_A',(.55,.43,.36))]):stone('SM_Stone_'+name,sc,480+i,name=='Mossy_A')

def blade(verts,faces,mids,base,forward,length,width,matidx):
    base=Vector(base);forward=Vector(forward).normalized();right=forward.cross(Vector((0,0,1)))
    if right.length<.01:right=Vector((1,0,0))
    right.normalize();normal=right.cross(forward).normalized();start=len(verts)
    # Closed rounded leaf outline and folded ridge: 8 triangles, no rectangle.
    outline=[(0,0),(.22,-.67),(.52,-1),(.81,-.70),(1,0),(.81,.70),(.52,1),(.22,.67)]
    for t,w in outline:verts.append(tuple(base+forward*(t*length)+right*(w*width)+normal*(math.sin(t*math.pi)*length*.05)))
    verts.append(tuple(base+forward*length*.51+normal*length*.115))
    for i in range(8):faces.append((start+i,start+(i+1)%8,start+8));mids.append(matidx)

def plant(name,seed,tall=False,rosette=False):
    rand=random.Random(seed);verts=[];faces=[];mids=[];count=13 if rosette else (18 if tall else 16)
    for i in range(count):
        a=i*2.399963;rad=rand.uniform(.015,.15);base=(math.cos(a)*rad,math.sin(a)*rad,0)
        if rosette:
            length=rand.uniform(.24,.40);direction=(math.cos(a),math.sin(a),rand.uniform(.3,.7));width=length*.27
            blade(verts,faces,mids,base,direction,length,width,i%3)
        else:
            h=rand.uniform(.38,.68) if tall else rand.uniform(.19,.36);width=rand.uniform(.032,.055)
            side=Vector((-math.sin(a),math.cos(a),0));start=len(verts);base=Vector(base)
            for k in range(4):
                t=k/3;c=base+Vector((math.cos(a)*h*.52*t*t,math.sin(a)*h*.52*t*t,h*t));w=width*(1-t)**.7
                verts.extend([tuple(c-side*w),tuple(c+side*w)])
            for k in range(2):q=start+k*2;faces.append((q,q+1,q+3,q+2));mids.append(i%3)
            faces.append((start+4,start+5,start+6));mids.append(i%3)
    o=mesh(name,verts,faces,green,library,mids=mids)
    return o

def flowers(name,seed,lavender=False):
    rand=random.Random(seed);parts=[];verts=[];faces=[];mids=[]
    for i in range(5):
        a=i*2.399963;rad=.12+.09*(i%2);x=math.cos(a)*rad;y=math.sin(a)*rad;h=rand.uniform(.28,.48)
        parts.append(tube('FlowerStem',[(x,y,0),(x+.035,y,h*.52),(x+.055,y,h)],[.012,.009,.005],library,sides=5,steps=1,record=False,mat=green[0]))
        levels=3 if lavender else 1
        for level in range(levels):
            center=Vector((x+.055,y,h-level*.075));size=.06 if lavender else .073
            for petal in range(5):
                angle=petal*math.tau/5+level*.6
                blade(verts,faces,mids,center,(math.cos(angle),math.sin(angle),.08 if not lavender else .6),size,size*.36,1 if lavender else 0)
            # Low-poly domed pollen center.
            start=len(verts);verts.append(tuple(center+Vector((0,0,.02))))
            for k in range(8):verts.append(tuple(center+Vector((.026*math.cos(k*math.tau/8),.026*math.sin(k*math.tau/8),0))))
            for k in range(8):faces.append((start,start+1+k,start+1+(k+1)%8));mids.append(2)
        for side in [-1,1]:blade(verts,faces,mids,(x+.02,y,h*.40),(side*.6,.2,.5),.13,.032,3)
    parts.append(mesh('Petals',verts,faces,[cream,purple,gold,green[1]],library,mids=mids))
    return finish_module(parts,name)

register(plant('SM_Grass_Short_A',201));register(plant('SM_Grass_Short_B',215));register(plant('SM_Grass_Tall_A',208,tall=True))
register(plant('SM_GroundPlant_A',207,rosette=True))
pb=plant('SM_GroundPlant_B',241,rosette=True)
for v in pb.data.vertices:v.co.z*=1.5;v.co.x*=.77
register(pb)
flowers('SM_FlowerCluster_A',304);flowers('SM_FlowerCluster_B',311,True)
ga=plant('GrassFlowerBase',318);fa=flowers('Temp_Flowers',328);modules.remove(fa);finish_module([ga,fa],'SM_Grass_Flowers_A')
verts=[];faces=[];mids=[]
for i in range(11):
    a=i*2.399;rad=.11+.029*i
    blade(verts,faces,mids,(math.cos(a)*rad,math.sin(a)*rad,.016),(math.cos(a+.4),math.sin(a+.4),.035),.14+.014*(i%3),.042,i%3)
register(mesh('SM_GroundLeaves_A',verts,faces,green,library,mids=mids))

def instance(template,col,pos=(0,0,0),scale=1,rotation=0):
    o=template.copy();o.data=template.data;col.objects.link(o);o.location=pos;o.scale=(scale,)*3;o.rotation_euler.z=rotation;o.hide_render=False;o.hide_set(False);return o
def module(name):return next(o for o in modules if o.name==name)
for flowered in [False,True]:
    verts=[(0,0,.035)];faces=[]
    for i in range(24):
        a=i*math.tau/24;rad=1+.07*math.sin(5*a)+.03*math.cos(9*a)
        verts.append((math.cos(a)*rad,math.sin(a)*rad*.83,-.018))
    for i in range(24):faces.append((0,1+i,1+(i+1)%24))
    parts=[mesh('SoilPatch',verts,faces,[soil],library)]
    for i in range(9):
        a=i*math.tau/9;rad=.65+.14*math.sin(i*3)
        template=module('SM_FlowerCluster_A' if flowered and i%3==0 else 'SM_Grass_Short_A')
        parts.append(instance(template,library,(math.cos(a)*rad,math.sin(a)*rad*.83,0),.65,i*.8))
    parts.append(instance(module('SM_GroundLeaves_A'),library,(-.2,.1,.03),1.1))
    finish_module(parts,'SM_GroundPatch_Flowers_A' if flowered else 'SM_GroundPatch_A')

# Optional presentation dressing remains separately selectable and is NOT baked into tree.
for i in range(25):
    a=i*2.399963;rad=1.1+.65*((i%7)/6)
    name=['SM_Grass_Short_A','SM_GroundPlant_A','SM_Grass_Short_B','SM_FlowerCluster_A','SM_FlowerCluster_B'][i%5]
    instance(module(name),ground_col,(math.cos(a)*rad,math.sin(a)*rad,.005),.8+.2*(i%3),a)
for name,pos,s in [('SM_Stone_Medium_A',(-1.31,-.62,-.02),1),('SM_Stone_Small_B',(.70,-1.28,-.01),1),('SM_Stone_Mossy_A',(1.24,.49,-.015),.86),('SM_Stone_Small_A',(-.64,1.25,-.01),1)]:instance(module(name),ground_col,pos,s)

# One palette material for opaque kit meshes, rather than 3-7 draw calls per clump.
palette_mats=green+stone_mats+[moss,soil,cream,gold,purple,dark]
N=64;pixels=np.ones((N,N,4),dtype=np.float32)
for i,m in enumerate(palette_mats):
    color=m.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value
    x=(i%4)*16;y=(i//4)*16;pixels[y:y+16,x:x+16]=color
im=bpy.data.images.new('T_Oak_Kit_Palette',width=N,height=N,alpha=False);im.pixels.foreach_set(pixels.ravel())
im.filepath_raw=os.path.join(ROOT,'Textures','T_Oak_Kit_Palette.png');im.file_format='PNG';im.save()
palette=material('M_Oak_Kit_Palette',(.3,.3,.2));t=texture(palette,im.filepath_raw)
palette.node_tree.links.new(t.outputs['Color'],palette.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
for o in modules:
    if not all(m in palette_mats for m in o.data.materials):continue
    uv=o.data.uv_layers[0] if o.data.uv_layers else o.data.uv_layers.new(name='UV0')
    for face in o.data.polygons:
        idx=palette_mats.index(o.data.materials[face.material_index]);coord=((idx%4+.5)/4,(idx//4+.5)/4)
        for li in face.loop_indices:uv.data[li].uv=coord
        face.material_index=0
    o.data.materials.clear();o.data.materials.append(palette)
library.hide_render=True;library.hide_viewport=True
game=copy_join([wood,rim]+canopy,'SM_Tree_Oak_A',exports)
game['asset_role']='Final gameplay LOD0, dressing exported separately'
game['dimensions_units']='metres; intended scale in Unity is 1 unit = 1 metre'
lods=[game]
for level,ratio in [(1,.60),(2,.28)]:
    # Keep every whole cluster while reducing curved patches from 8 to 4 or 2 tris.
    copies=[]
    for ob in [wood,rim]:
        c=ob.copy();c.data=ob.data.copy();exports.objects.link(c);simplify(c,.59 if level==1 else .26);copies.append(c)
    for ob in canopy:
        verts=[];faces=[];uv=[];me=ob.data
        for start in range(0,len(me.vertices),9):
            ids=[0,2,8,6,4] if level==1 else [0,2,8,6]
            offset=len(verts)
            for idx in ids:verts.append(tuple(me.vertices[start+idx].co))
            uvbyvert={loop.vertex_index:tuple(me.uv_layers[0].data[loop.index].uv) for loop in me.loops if start<=loop.vertex_index<start+9}
            for idx in ids:uv.append(uvbyvert[start+idx])
            if level==1:
                for j in range(4):faces.append((offset+j,offset+(j+1)%4,offset+4))
            else:faces.append((offset,offset+1,offset+2,offset+3))
        copies.append(mesh('ReducedLeafMass',verts,faces,[leaf],exports,uv))
    o=copy_join(copies,'SM_Tree_Oak_A_LOD'+str(level),exports)
    for c in copies:bpy.data.objects.remove(c,do_unlink=True)
    lods.append(o)

collision=tube('COL_Trunk_Guide',[(0,0,.02),(0,0,1.4),(.16,.06,2.7)],[.53,.51,.43],exports,sides=10,steps=1,record=False)
collision.display_type='WIRE';collision.hide_render=True;collision.hide_set(True)
collision['usage']='Optional collider reference in Blender only; not included in FBX. Use a capsule collider in Unity.'
stats={}
def stats_for(o):
    o.data.calc_loop_triangles()
    return {'triangles':len(o.data.loop_triangles),'vertices':len(o.data.vertices),'materials':[m.name for m in o.data.materials],'dimensions_m':[round(x,4) for x in o.dimensions],'uv_layers':[uv.name for uv in o.data.uv_layers]}
def export(o,extra=None):
    active(o)
    if o.data.users>1:o.data=o.data.copy()
    tri=o.modifiers.new('Explicit export triangulation','TRIANGULATE');tri.quad_method='FIXED'
    if hasattr(tri,'keep_custom_normals'):tri.keep_custom_normals=True
    bpy.ops.object.modifier_apply(modifier=tri.name)
    o.data.validate();o.data.update()
    for c in extra or []:c.hide_set(False);c.select_set(True)
    bpy.ops.export_scene.fbx(filepath=os.path.join(ROOT,'Exports',o.name+'.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',use_mesh_modifiers=True,mesh_smooth_type='FACE',bake_anim=False,path_mode='RELATIVE',embed_textures=False,use_custom_props=True)
    stats[o.name]=stats_for(o)
    for c in extra or []:c.hide_set(True)

# Give each standalone module UV0, even when its material is a simple constant.
library.hide_viewport=False
for o in modules:
    if not o.data.uv_layers:
        active(o);bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(island_margin=.015);bpy.ops.object.mode_set(mode='OBJECT')
    export(o);o.hide_set(True)
library.hide_viewport=True
for i,o in enumerate(lods):export(o);o.hide_render=True;o.hide_set(True)
exports.hide_render=True
for im in bpy.data.images:
    if im.source=='FILE':im.pack()

manifest={'asset_count':len(modules)+1,'lod_count':len(lods),'assets':stats,'canopy_masses':len(masses),'canopy_cards':sum(o['cluster_groups'] for o in canopy),'primary_branches':len(primary),'roots':len(root_specs),'source_textures_reused':[os.path.join(MAT,'T_Foliage','T_Foliage_BaseColor.png'),os.path.join(MAT,'Bark','Bark_BaseColor.png'),os.path.join(MAT,'Bark','Bark_Normal.png')],'notes':['Bark mixes a broad procedural tile with the existing painted Bark set; oriented along growth.','FieldStone depicts masonry; coordinated solid palette used for individual stones.','Ground decoration is optional and separate from SM_Tree_Oak_A.','Target engine: Unity. Y-up FBX, -Z forward, metre scene. Engine testing intentionally deferred.','Foliage requires alpha clipping and double-sided rendering. Existing BaseColor RGBA supplies opacity.','FBXs contain only the asset mesh, no UCX collider. Optional collider guide stays in Blender.','Assign the three tree meshes to a Unity LODGroup later.','Blender shader graphs do not transfer through FBX; reproduce material settings from README.','Canopy enlarged by mass, without increasing card count or triangles.']}
with open(os.path.join(ROOT,'QA','asset_manifest.json'),'w',encoding='utf8') as f:json.dump(manifest,f,indent=2,ensure_ascii=False)
material_spec={}
for m in bpy.data.materials:
    if not m.name.startswith('M_'):continue
    p=m.node_tree.nodes.get('Principled BSDF')
    material_spec[m.name]={'base_color_linear':list(p.inputs['Base Color'].default_value),'roughness':p.inputs['Roughness'].default_value,'two_sided':m.name.startswith(('M_Plant','M_Petal','M_Pollen','M_Oak_Foliage'))}
with open(os.path.join(ROOT,'QA','material_spec.json'),'w') as f:json.dump(material_spec,f,indent=2)
scene.render.resolution_x=1400;scene.render.resolution_y=1400;scene.cycles.samples=48
render('03_hero',(8,-17,8),(0,0,3.45),9.0,1400)
render('03_gameplay',(9,-13,13),(0,0,3.3),10.0,1200)
render('03_front',(0,-18,6),(0,0,3.45),8.8,1000)
render('03_back',(0,18,6),(0,0,3.45),8.8,1000)
render('03_left',(-18,0,6),(0,0,3.45),8.8,1000)
render('03_right',(18,0,6),(0,0,3.45),8.8,1000)
render('03_top',(0,0,18),(0,0,0),8.8,1000)
render('03_trunk_detail',(3,-8,3.8),(0,0,1.5),3.8,1200)
# Verify the actual joined gameplay mesh and each LOD, using identical framing.
tree.hide_render=True;ground_col.hide_render=True;exports.hide_render=False
for i,o in enumerate(lods):
    o.hide_render=False;render('04_LOD'+str(i)+'_gameplay',(9,-13,13),(0,0,3.3),10.0,1000);o.hide_render=True
exports.hide_render=True;tree.hide_render=False;ground_col.hide_render=False
scene.camera.location=(8,-17,8);scene.camera.rotation_euler=(Vector((0,0,3.45))-scene.camera.location).to_track_quat('-Z','Y').to_euler();scene.camera.data.ortho_scale=9.0
# Material preview and studio render are ready when the user opens the source.
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_perspective='CAMERA';area.spaces.active.shading.type='MATERIAL'
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,'Cozy_Oak_Kit.blend'))
print('KIT_COMPLETE',json.dumps({k:v['triangles'] for k,v in stats.items()}),flush=True)
