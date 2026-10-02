"""Directed botanical hierarchy / buttress-root sculpt on the existing Tree03 asset.
Blender 4.4. No mutation of prior assets. Run --final for full resolution renders.
"""
import bpy,bmesh,math,random,os,json,sys
from mathutils import Vector,Quaternion
ROOT=os.path.dirname(os.path.abspath(__file__))
OUT=os.path.join(ROOT,'Tree_04');os.makedirs(OUT,exist_ok=True)
MAT=os.path.abspath(os.path.join(ROOT,'../../../Mat'))
FINAL='--final' in sys.argv
r=random.Random(9407)
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT,'Tree_03/Tree_03_Master.blend'))
scene=bpy.context.scene
for ob in list(bpy.data.objects):
    if 'Canopy' in ob.name or '_LOD1_' in ob.name or '_LOD2_' in ob.name:bpy.data.objects.remove(ob,do_unlink=True)
wood=bpy.data.objects['Tree03_LOD0_Trunk'];wood.name='Tree04_TrunkRoots_LOD0'
def active(ob):
    bpy.ops.object.select_all(action='DESELECT');ob.hide_viewport=False;ob.select_set(True);bpy.context.view_layer.objects.active=ob
def mesh(name,v,f,mats,uvs=None,mids=None):
    me=bpy.data.meshes.new(name);me.from_pydata(v,[],f);me.update();ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob)
    for m in mats:me.materials.append(m)
    for p in me.polygons:p.use_smooth=True;p.material_index=mids[p.index] if mids else 0
    if uvs:
        uv=me.uv_layers.new(name='UVMap')
        for p in me.polygons:
            for li in p.loop_indices:uv.data[li].uv=uvs[me.loops[li].vertex_index]
    return ob
def mat(name,col):
    m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*col,1);p.inputs['Roughness'].default_value=.83;return m,p
def tex(m,path,linear=False):
    im=bpy.data.images.load(os.path.join(MAT,path),check_existing=True)
    im.colorspace_settings.name='Non-Color' if linear else 'sRGB';im.pack()
    node=m.node_tree.nodes.new('ShaderNodeTexImage');node.image=im;return node

# Remove only the defective original foot; keep the successful branch network.
bm=bmesh.new();bm.from_mesh(wood.data)
result=bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=.00001,plane_co=(0,0,1.28),plane_no=(0,0,1),clear_inner=True)
boundary=[e for e in bm.edges if e.is_boundary]
if boundary:bmesh.ops.holes_fill(bm,edges=boundary,sides=0)
bm.to_mesh(wood.data);bm.free()

# One continuous flare, not six attached cones. Unequal buttress heights and widths.
roots=[(-2.55,1.12,.79,.24),(-1.46,1.26,1.06,.25),(-.30,.97,.72,.23),(.62,.86,.68,.25),(1.65,1.12,.88,.27),(2.50,.65,.64,.23)]
v=[];f=[];sides=120;rings=45
for k in range(rings):
    z=-.32+k*(2.11/(rings-1));c=Vector((-.055*math.sin(z*1.4),.018,z))
    for j in range(sides):
        a=j*math.tau/sides;core=.505+.095*math.exp(-max(0,z)/.65)
        ext=0
        for angle,length,height,width in roots:
            da=math.atan2(math.sin(a-angle-.065*math.sin(z*2)),math.cos(a-angle-.065*math.sin(z*2)))
            # Broad vertical buttress with shoulders that descend into the soil.
            profile=math.exp(-((max(0,z)+.09)/(height*.59))**1.46)
            ext+=length*profile*math.exp(-.5*(da/width)**2)
        rad=core+ext+.018*math.sin(a*5+z*2)
        v.append(tuple(c+Vector((math.cos(a)*rad,math.sin(a)*rad,0))))
for k in range(rings-1):
    for j in range(sides):a=k*sides+j;b=k*sides+(j+1)%sides;f.append((a,b,b+sides,a+sides))
f.extend([tuple(reversed(range(sides))),tuple((rings-1)*sides+j for j in range(sides))])
flare=mesh('ContinuousRootFlare',v,f,[wood.data.materials[0]])
active(wood);flare.select_set(True);bpy.ops.object.join()
rem=wood.modifiers.new('Blend only root transition and branch junctions','REMESH');rem.mode='VOXEL';rem.voxel_size=.039;bpy.ops.object.modifier_apply(modifier=rem.name)
sm=wood.modifiers.new('Rounded bark foundation','SMOOTH');sm.factor=.48;sm.iterations=3;bpy.ops.object.modifier_apply(modifier=sm.name)

# Use the original major branch paths as a coordinate field for grain / relief.
paths=[[(0,0,-.2),(-.1,.02,1.2),(.18,.08,2.72),(-.48,.12,4.05),(-.78,.15,4.78)],[(.08,.03,1.55),(.92,.1,3),(1.3,.06,3.88),(.78,.18,5.72)],[(-.02,0,2.2),(-1.42,-.16,3.32),(-2.82,-.04,4.35)],[(.12,.1,2.46),(.15,.72,3.12),(-.52,1.92,4.55)],[(.54,.04,2.62),(1.32,-.28,3.2),(2.65,-.48,4.35)]]
segments=[]
for pi,path in enumerate(paths):
    dist=0
    for aa,bb in zip(path,path[1:]):
        a,b=Vector(aa),Vector(bb);axis=(b-a).normalized();length=(b-a).length;u=axis.cross(Vector((0,1,0))).normalized();vv=axis.cross(u).normalized()
        segments.append((a,axis,length,u,vv,dist,pi));dist+=length
def field(co):
    eligible=[s for s in segments if s[6]==0] if co.z<2.5 else segments
    s=min(eligible,key=lambda s:(co-s[0]-s[1]*max(0,min(s[2],(co-s[0]).dot(s[1])))).length_squared)
    a,axis,length,u,vv,dist,pi=s;q=co-a
    return math.atan2(q.dot(vv),q.dot(u)),q.dot(axis)+dist,pi
depth=[]
for vert in wood.data.vertices:
    co=vert.co;a,z,pi=field(co)
    phase=a*11+.55*math.sin(z*1.8)+.18*math.sin(z*5+a*3)
    ridge=(.5+.5*math.cos(phase))**1.8
    medium=.5+.5*math.cos(a*21+.9*math.sin(z*2.2)+.35*math.sin(z*5))
    amp=.040 if co.z<3.3 else .020
    # Long relief affects silhouette and shadows. Fine texture remains in the shader.
    vert.co+=vert.normal*(amp*(ridge-.38)+.014*(medium-.5))
    depth.append(.25+.55*ridge+.12*medium)
wood.data.update()
active(wood)
smooth=wood.modifiers.new('Soften longitudinal plate edges','SMOOTH');smooth.factor=.45;smooth.iterations=2;bpy.ops.object.modifier_apply(modifier=smooth.name)
for p in wood.data.polygons:p.use_smooth=True
attr=wood.data.color_attributes.new(name='BarkForm',type='FLOAT_COLOR',domain='POINT')
for item,d in zip(attr.data,depth):item.color=(d,d,d,1)
uv=wood.data.uv_layers.new(name='BarkFlow')
for poly in wood.data.polygons:
    coords=[]
    for li in poly.loop_indices:
        a,z,pi=field(wood.data.vertices[wood.data.loops[li].vertex_index].co);coords.append((li,a/math.tau,z*.42))
    crossing=max(x[1] for x in coords)-min(x[1] for x in coords)>.5
    for li,a,z in coords:uv.data[li].uv=(a+1 if crossing and a<0 else a,z)
wood.data.uv_layers.active=uv

bark,p=mat('M_Tree04_Bark_Layered',(.27,.18,.11));n=bark.node_tree.nodes;l=bark.node_tree.links
form=n.new('ShaderNodeVertexColor');form.layer_name='BarkForm'
ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.1;ramp.color_ramp.elements[0].color=(.12,.078,.044,1);ramp.color_ramp.elements[1].position=.95;ramp.color_ramp.elements[1].color=(.32,.235,.145,1)
l.new(form.outputs['Color'],ramp.inputs[0])
bc=tex(bark,'Bark/Bark_BaseColor.png');sat=n.new('ShaderNodeHueSaturation');sat.inputs['Saturation'].default_value=.65;l.new(bc.outputs['Color'],sat.inputs['Color'])
mix=n.new('ShaderNodeMixRGB');mix.blend_type='MIX';mix.inputs[0].default_value=.72;l.new(ramp.outputs['Color'],mix.inputs[1]);l.new(sat.outputs['Color'],mix.inputs[2]);l.new(mix.outputs[0],p.inputs['Base Color'])
normal=tex(bark,'Bark/Bark_Normal.png',True);nm=n.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.36;l.new(normal.outputs['Color'],nm.inputs['Color'])
height=tex(bark,'Bark/Bark_Displacement.png',True);bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.30;bump.inputs['Distance'].default_value=.04;l.new(height.outputs['Color'],bump.inputs['Height']);l.new(nm.outputs['Normal'],bump.inputs['Normal']);l.new(bump.outputs['Normal'],p.inputs['Normal'])
rough=tex(bark,'Bark/Bark_Roughness.png',True);rr=n.new('ShaderNodeMapRange');rr.inputs['To Min'].default_value=.67;rr.inputs['To Max'].default_value=.94;l.new(rough.outputs['Color'],rr.inputs['Value']);l.new(rr.outputs['Result'],p.inputs['Roughness'])
p.inputs['Specular IOR Level'].default_value=.24
wood.data.materials.clear();wood.data.materials.append(bark)
for p in wood.data.polygons:p.material_index=0
# Keep the hollow and its outline; give the rim a calm matching wood material.
rim=bpy.data.objects['Tree02_OldKnot_Rim'];rim_mat,_=mat('M_Knot_Rim',(.23,.145,.078));rim.data.materials.clear();rim.data.materials.append(rim_mat)
# Seat the existing hollow on the changed surface and carve a shallow real cavity.
hit,location,normal,index=wood.ray_cast(Vector((.12,-3,1.18)),Vector((0,1,0)))
if hit:
    front=location.y;rim.location.y=front-.018
    dark=bpy.data.objects['Tree02_OldKnot_Recess'];dark.location.y=front-.024
assert len(wood.data.polygons)>15000,'Trunk surface was lost'

leaf,p=mat('M_Tree04_Leaf_Atlas',(.25,.35,.08));n=leaf.node_tree.nodes;l=leaf.node_tree.links
leaftex=tex(leaf,'T_Foliage/T_Foliage_BaseColor.png')
tint=n.new('ShaderNodeVertexColor');tint.layer_name='LeafTint';mix=n.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1;l.new(leaftex.outputs['Color'],mix.inputs[1]);l.new(tint.outputs['Color'],mix.inputs[2]);l.new(mix.outputs[0],p.inputs['Base Color'])
alpha=n.new('ShaderNodeMath');alpha.operation='GREATER_THAN';alpha.inputs[1].default_value=.56;l.new(leaftex.outputs['Alpha'],alpha.inputs[0]);l.new(alpha.outputs[0],p.inputs['Alpha'])
p.inputs['Roughness'].default_value=.86;p.inputs['Specular IOR Level'].default_value=.10;p.inputs['Subsurface Weight'].default_value=.055
leaf.surface_render_method='DITHERED';leaf.use_transparency_overlap=False;leaf.use_backface_culling=False
twigmat,_=mat('M_Tree04_YoungTwigs',(.20,.125,.052))

# Endpoint coordinates measured from the actual leaf atlas, top-origin pixel space.
# Different source leaves have different base->tip directions. Geometry is based at petiole.
leaves=[{'rect':(22,976,213,1212),'base':(198,1202),'tip':(34,980)},
        {'rect':(221,983,423,1214),'base':(243,1205),'tip':(412,990)},
        {'rect':(910,985,1066,1215),'base':(945,1203),'tip':(1048,1009)},
        {'rect':(1072,983,1246,1215),'base':(1109,1205),'tip':(1215,996)}]
leaf_audit=[]
def append_tube(v,f,points,radii,sides=6):
    base=len(v)
    for i,(p,rad) in enumerate(zip(points,radii)):
        axis=(points[min(i+1,len(points)-1)]-points[max(i-1,0)]).normalized();u=axis.cross(Vector((0,0,1)))
        if u.length<.1:u=axis.cross(Vector((0,1,0)))
        u.normalize();vv=axis.cross(u)
        for j in range(sides):ang=j*math.tau/sides;v.append(tuple(p+rad*(u*math.cos(ang)+vv*math.sin(ang))))
    for i in range(len(points)-1):
        for j in range(sides):a=base+i*sides+j;b=base+i*sides+(j+1)%sides;f.append((a,b,b+sides,a+sides))

library=bpy.data.collections.new('Reusable_Shoot_Library');scene.collection.children.link(library);library.hide_render=True;library.hide_viewport=True
prototypes=[]
for variant in range(9):
    lv=[];lf=[];uvs=[];cols=[];tv=[];tf=[]
    length=.39+.025*(variant%3);count=18
    # Three short overlapping branchlets give one rounded, volumetric leaf cluster.
    ends=[Vector((-.22,length,.095)),Vector((.23,length*.88,.025)),Vector((.01,length*1.32,.18))]
    for end in ends:append_tube(tv,tf,[Vector((0,0,0)),end*.53,end],[.006,.004,.001],4)
    for j in range(count):
        branchlet=j//6;t=.19+.15*(j%6);side=1 if j%2 else -1
        anchor=ends[branchlet]*t
        forward=Vector((side*r.uniform(.56,.90)+ends[branchlet].x*.7,r.uniform(.65,.95),r.uniform(-.03,.22))).normalized()
        forward.rotate(Quaternion(Vector((0,0,1)),r.uniform(-.15,.15)))
        petiole=anchor+forward*.045
        # Thin petiole ribbon; its endpoints still connect leaf base to the shoot.
        sidevec=Vector((-.0025,0,.001));q=len(tv);tv.extend([tuple(anchor-sidevec),tuple(anchor+sidevec),tuple(petiole+sidevec*.5),tuple(petiole-sidevec*.5)]);tf.append((q,q+1,q+2,q+3))
        up=Vector((0,0,1));right=forward.cross(up).normalized();normal=right.cross(forward).normalized()
        normal.rotate(Quaternion(forward,side*.63+r.uniform(-.20,.20)));right=forward.cross(normal).normalized()
        blade_len=r.uniform(.255,.32)*(1-.10*t);idx=(j+variant)%len(leaves);spec=leaves[idx]
        b=Vector(spec['base']);tip=Vector(spec['tip']);direction=(tip-b).normalized();perp=Vector((-direction.y,direction.x));pixel_length=(tip-b).length
        x0,y0,x1,y1=spec['rect'];base=len(lv)
        for yy in range(3):
            for xx in range(3):
                pixel=Vector((x0+(x1-x0)*xx/2,y0+(y1-y0)*yy/2));delta=pixel-b
                along=delta.dot(direction)/pixel_length;across=delta.dot(perp)/pixel_length
                bend=.014*math.sin(max(0,min(1,along))*math.pi)-.008*abs(across)
                lv.append(tuple(petiole+forward*(along*blade_len)+right*(across*blade_len)+normal*bend));uvs.append((pixel.x/1254,1-pixel.y/1254))
                s=.89+.07*variant/8+r.uniform(-.025,.025);cols.append((s,s*.99,s*.92,1))
        for yy in range(2):
            for xx in range(2):a=base+yy*3+xx;lf.append((a,a+3,a+4,a+1))
        leaf_audit.append({'variant':variant,'leaf':j,'atlas':idx,'growth_dot':forward.y,'petiole':list(petiole),'tip':list(petiole+forward*blade_len)})
    lo=mesh('ShootLeaves_%02d'%variant,lv,lf,[leaf],uvs);c=lo.data.color_attributes.new(name='LeafTint',type='FLOAT_COLOR',domain='POINT')
    for item,col in zip(c.data,cols):item.color=col
    to=mesh('ShootStem_%02d'%variant,tv,tf,[twigmat])
    for ob in [lo,to]:
        for co in list(ob.users_collection):co.objects.unlink(ob)
        library.objects.link(ob)
    prototypes.append((lo.data,to.data))

# Directed hierarchy: preserved major branch -> secondary -> terminal shoot -> leaf petiole.
hier=bpy.data.objects.new('Tree04_BotanicalHierarchy',None);bpy.context.collection.objects.link(hier)
masses=[('Central',(-.45,.30,5.58),(1.42,1.30,1.35),(-.48,.12,4.05),90),
('Top',(.25,.22,6.12),(1.04,.97,.80),(.78,.18,5.45),62),
('Left',(-2.13,-.03,4.66),(1.19,1.05,1.12),(-1.7,-.15,3.6),72),
('Right',(1.95,-.36,4.92),(1.04,.97,1.14),(2.05,-.5,3.82),68),
('Front',(-.51,-1.03,4.76),(1.23,.86,1.02),(-.65,-.06,3.12),65),
('Back',(-.22,1.38,5.15),(1.18,.88,1.12),(-.05,1.38,3.78),66),
('HighRight',(1.15,.55,5.67),(.92,.90,.99),(1.12,.12,4.82),56)]
branchv=[];branchf=[];instances=[];shoot_meta=[]
for name,cc,radii,attachment,count in masses:
    center=Vector(cc);root=Vector(attachment);mass=bpy.data.objects.new('CrownMass_'+name,None);bpy.context.collection.objects.link(mass);mass.parent=hier
    for j in range(count):
        # Stratified directions form overlapping volumes and leave deliberate crown gaps.
        z=1-2*(j+.5)/count;phi=j*2.399963+.7*r.random();rad=math.sqrt(max(0,1-z*z))
        d=Vector((rad*math.cos(phi),rad*math.sin(phi),z))
        radius=.46 if j%5==0 else r.uniform(.77,1.0)
        target=center+Vector((d.x*radii[0],d.y*radii[1],d.z*radii[2]))*radius
        elbow=root.lerp(center,.62)+Vector((d.x*.20,d.y*.20,.03))
        endpoint=target
        if j%4==0:append_tube(branchv,branchf,[root,elbow,endpoint],[.018,.010,.003],5)
        axis=(endpoint-elbow).normalized()
        outward=(target-center).normalized();vertical=Vector((0,0,1));side=axis.cross(vertical)
        if side.length<.1:side=Vector((1,0,0))
        side.normalize()
        for k in range(1):
            origin=endpoint
            growth=(axis*.72+outward*.35+side*((-1 if k%2 else 1)*.36)+vertical*.15).normalized()
            # Shoots bend toward crown light; leaves lie at a shallow angle to the sky.
            growth.z=max(-.24,min(.30,growth.z));growth.normalize()
            quat=growth.to_track_quat('Y','Z');quat=quat@Quaternion(Vector((0,1,0)),r.uniform(-.32,.32))
            variant=(j+k*2)%9;scale=r.uniform(.90,1.18)
            # Terminal shoots reach outward from their branch, never arbitrary centers.
            for kind,data in zip(['LeafShoot','TwigShoot'],prototypes[variant]):
                ob=bpy.data.objects.new(name+'_'+kind+'_%03d_%d'%(j,k),data);bpy.context.collection.objects.link(ob);ob.location=origin;ob.rotation_mode='QUATERNION';ob.rotation_quaternion=quat;ob.scale=(scale,)*3;ob.parent=mass
                instances.append(ob)
            shoot_meta.append({'mass':name,'parent_branch':j,'origin':list(origin),'direction':list(growth),'prototype':variant,'scale':scale})
branches=mesh('Tree04_SecondaryBranches',branchv,branchf,[twigmat]);branches.parent=hier
assert min(a['growth_dot'] for a in leaf_audit)>.4

# Softer volumetric infill from the existing cluster atlas, mixed with directed outer shoots.
# These cards represent complete small leaf groups, not individually random leaves.
fillv=[];fillf=[];filluv=[];fillcols=[]
cluster_rects=[(14,22,452,414),(468,12,863,422),(873,28,1244,403)]
for mi,(name,cc,radii,attachment,count) in enumerate(masses):
    center=Vector(cc)
    for j in range(count):
        z=1-2*(j+.5)/count;phi=j*2.399963+mi*.75;rad=math.sqrt(max(0,1-z*z));d=Vector((rad*math.cos(phi),rad*math.sin(phi),z))
        position=center+Vector((d.x*radii[0],d.y*radii[1],d.z*radii[2]))*r.uniform(.75,1.00)
        normal=Vector((d.x*.82,d.y*.82,.52+d.z*.34)).normalized()
        up=Vector((0,0,1));right=normal.cross(up)
        if right.length<.1:right=Vector((1,0,0))
        right.normalize();vertical=right.cross(normal).normalized()
        size=r.uniform(.63,.86);x0,y0,x1,y1=cluster_rects[(j+mi)%3];base=len(fillv)
        for yy in range(3):
            for xx in range(3):
                x=xx/2;y=yy/2;bend=.06*(1-4*(x-.5)**2)*(1-4*(y-.5)**2)
                fillv.append(tuple(position+right*((x-.5)*size)+vertical*((y-.5)*size)+normal*bend));filluv.append(((x0+x*(x1-x0))/1254,1-(y1-y*(y1-y0))/1254));fillcols.append((.94,.97,.9,1))
        for yy in range(2):
            for xx in range(2):a=base+yy*3+xx;fillf.append((a,a+1,a+4,a+3))
infill=mesh('Tree04_Crown_VolumeInfill',fillv,fillf,[leaf],filluv);infill.parent=hier
col=infill.data.color_attributes.new(name='LeafTint',type='FLOAT_COLOR',domain='POINT')
for item,value in zip(col.data,fillcols):item.color=value

# Keep props, positions, scale and the existing main branches. Presentation lights expose relief.
for ob in bpy.data.objects:
    if ob.type=='LIGHT' and ob.data.type=='POINT':ob.data.energy=2
    if ob.type=='LIGHT' and ob.data.type=='AREA':
        if ob.location.y<0:ob.data.energy=2000;ob.data.size=4;ob.data.color=(1,.88,.70)
        else:ob.data.energy=850;ob.data.size=5;ob.data.color=(.80,.88,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.45
scene.render.engine='CYCLES';scene.cycles.samples=48 if FINAL else 20;scene.cycles.use_denoising=True
try:
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
    for device in prefs.devices:device.use=device.type=='OPTIX'
    scene.cycles.device='GPU'
except Exception:pass
scene.cycles.transparent_max_bounces=16
scene.render.resolution_x=1500 if FINAL else 1050;scene.render.resolution_y=scene.render.resolution_x;scene.render.resolution_percentage=100
scene.view_settings.look='AgX - Medium High Contrast'
def camera(pos,target,scale):
    cam=scene.camera;cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
camera((8,-16,8),(-.15,0,3.05),9.6)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'Tree_04_Master.blend'))
with open(os.path.join(OUT,'growth_audit.json'),'w') as out:json.dump({'leaf_sources':leaves,'prototype_leaves':leaf_audit,'shoots':shoot_meta,'root_directions':roots},out,indent=2)
views=[('hero',(8,-16,8),(-.15,0,3.05),9.6),('detail',(3,-10,4.2),(0,-.05,1.65),4.5),('game',(8,-16,11),(0,0,3),17),('rear',(-9,13,7),(0,0,3.05),9.6)]
for label,pos,target,scale in views:
    camera(pos,target,scale);scene.render.filepath=os.path.join(OUT,'Tree_04_'+label+'.png');bpy.ops.render.render(write_still=True)
print('TREE04_REWORK_DONE',len(shoot_meta),'shoots',sum(len(a.data.polygons) for a in instances if 'LeafShoot' in a.name),'leaf faces',flush=True)
