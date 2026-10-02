"""Stage 2: refine Tree02 wood from saved v002, preserving crown and stones.
Blender --factory-startup -b --python build_wood.py -- --revision v003
"""
import argparse, hashlib, json, math, sys
from pathlib import Path
import bpy, bmesh
import numpy as np
from mathutils import Vector

parser=argparse.ArgumentParser()
parser.add_argument('--revision',default='v003')
parser.add_argument('--views',default='WoodClay,RootsClay,Wood,Roots,Front,Back,Left,Right,Top,Bottom,Perspective,Gameplay,UV_Check')
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
assert args.revision.isalnum() and args.revision not in ('v001','v002')
ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parents[2]
BASE=ROOT/'Source/v002/Tree02_Blockout.blend'
base_hash=hashlib.sha256(BASE.read_bytes()).hexdigest()
OUT=ROOT/'Source'/args.revision
RENDERS=ROOT/'Renders'/args.revision
QA=ROOT/'QA'/args.revision
for p in (OUT,RENDERS,QA): p.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(BASE))
scene=bpy.context.scene
canopy=bpy.data.collections['Canopy_Proxies_NOT_FINAL_LEAVES']
source=bpy.data.collections['02_EDITABLE_GROWTH_SOURCE']
trunk_col=bpy.data.collections['Trunk'];root_col=bpy.data.collections['Roots'];branch_col=bpy.data.collections['Branches']
wood_col=bpy.data.collections['Wood']
stones=bpy.data.collections['03_OPTIONAL_STONES_FROM_OAK_KIT']
studio=bpy.data.collections['90_PREVIEW_NOT_FOR_EXPORT']
clay=bpy.data.materials['BLOCKOUT_Wood_NoTexture']

def fingerprint(objects):
    data=[]
    for ob in sorted(objects,key=lambda o:o.name):
        data.append((ob.name,list(ob.location),list(ob.rotation_euler),list(ob.scale),[list(v.co) for v in ob.data.vertices],[list(p.vertices) for p in ob.data.polygons]))
    return hashlib.sha256(json.dumps(data).encode()).hexdigest()
canopy_before=fingerprint(canopy.objects)
stones_before=fingerprint(stones.objects)
specs=[(o.name,[list(p) for p in o['control_points_m']],list(o['control_radii_m']),o.users_collection[0].name) for o in source.all_objects]
for o in list(wood_col.objects)+list(source.all_objects): bpy.data.objects.remove(o,do_unlink=True)
source.hide_viewport=False

def active(ob):
    bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob

def sample(points,radii,steps=7):
    ps=[Vector(p) for p in points];out=[];rr=[]
    for i in range(len(ps)-1):
        a,b,c,d=ps[max(0,i-1)],ps[i],ps[i+1],ps[min(len(ps)-1,i+2)]
        for k in range(steps):
            t=k/steps
            out.append(.5*(2*b+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t))
            rr.append(radii[i]*(1-t)+radii[i+1]*t)
    return out+[ps[-1]],rr+[radii[-1]]

paths=[];parts=[]
def tube(name,points,radii,col,kind='branch',record=True):
    ps,rs=sample(points,radii)
    sides=40 if kind=='trunk' else 24
    vertices=[];faces=[];frames=[];prev=None;distance=0
    for i,(c,r) in enumerate(zip(ps,rs)):
        axis=(ps[min(i+1,len(ps)-1)]-ps[max(i-1,0)]).normalized()
        side=axis.cross(Vector((0,1,0))).normalized() if prev is None else (prev-axis*prev.dot(axis)).normalized()
        other=axis.cross(side).normalized();prev=side
        if i: distance+=(c-ps[i-1]).length
        twist=.47*distance+.12*math.sin(distance*1.7)
        # Flowing broad flutes, not high-frequency bark displacement.
        amplitude={'trunk':.125,'root':.12,'branch':.07,'buttress':.045}[kind]
        for j in range(sides):
            a=j*math.tau/sides
            f=1+amplitude*math.cos(4*(a-twist))+.035*math.sin(7*a-.8*distance)
            p=c+r*f*(math.cos(a)*side+math.sin(a)*other)
            if kind=='root': p.z=c.z+(p.z-c.z)*.92
            if p.z<-.08: p.z=-.08+(p.z+.08)*.18
            vertices.append(tuple(p))
        frames.append((side,other))
    for i in range(len(ps)-1):
        for j in range(sides):
            a=i*sides+j;b=i*sides+(j+1)%sides
            faces.append((a,b,b+sides,a+sides))
    faces += [tuple(reversed(range(sides))),tuple((len(ps)-1)*sides+j for j in range(sides))]
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(vertices,[],faces);mesh.update()
    bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
    ob=bpy.data.objects.new(name,mesh);col.objects.link(ob);mesh.materials.append(clay)
    for p in mesh.polygons:p.use_smooth=True
    ob['control_points_m']=points;ob['control_radii_m']=radii;ob['kind']=kind
    parts.append(ob)
    if record: paths.append((ps,rs,frames,name))
    return ob

root_revisions={
 'SRC_Root_01':([(-.41,-.04,1.35),(-.47,-.30,1.02),(-.12,-.45,.71),(.39,-.42,.41),(.95,-.46,.19),(1.40,-.51,.035),(1.78,-.53,-.075)],[.14,.21,.25,.255,.18,.082,.012]),
 'SRC_Root_02':([(-.35,-.10,1.60),(-.56,-.30,1.21),(-.37,-.52,.76),(.0,-.69,.38),(.13,-.98,.095),(.36,-1.17,-.08)],[.13,.17,.20,.19,.10,.015]),
 'SRC_Root_03':([(-.43,-.08,.94),(-.62,-.32,.53),(-.87,-.58,.25),(-1.13,-.79,.07),(-1.31,-.94,-.07)],[.20,.245,.18,.095,.013]),
 'SRC_Root_04':([(-.40,.02,.81),(-.67,.23,.48),(-1.00,.24,.25),(-1.22,.44,.08),(-1.41,.61,-.07)],[.19,.225,.16,.09,.012]),
 'SRC_Root_05':([(-.25,.08,1.10),(-.01,.35,.75),(.29,.49,.41),(.71,.83,.19),(1.08,1.06,-.07)],[.16,.20,.23,.15,.012]),
 'SRC_Root_06':([(-.37,.13,.78),(-.48,.41,.51),(-.57,.85,.21),(-.31,1.25,.04),(-.11,1.42,-.08)],[.18,.22,.16,.08,.012]),
 'SRC_Root_07':([(-.07,.13,.65),(.40,.18,.38),(.91,.29,.19),(1.12,.54,.04),(1.30,.72,-.08)],[.20,.23,.15,.075,.012])}
for name,p,r,col_name in specs:
    if name.startswith('SRC_Root'):
        p,r=root_revisions[name];kind='root'
    elif name=='SRC_Trunk_S_Curve':
        # Slight depth movement supports the twist on side views.
        p=[(0,0,-.12),(-.15,-.02,.38),(-.43,.015,.92),(-.45,.12,1.42),(-.15,.16,1.95),(.27,.065,2.48),(.40,.09,2.97),(.36,.12,3.38),(.65,.19,3.94),(1.03,.26,4.50)]
        r=[.46,.445,.415,.365,.325,.28,.22,.18,.13,.035];kind='trunk'
    else: kind='branch'
    p=[[float(x)*.96,float(y),float(z)] for x,y,z in p]
    tube(name,p,r,bpy.data.collections[col_name],kind)

# Shallow continuous buttress folds flowing through the lower trunk.
# Their centers stay inside the primary surface; no detached decorative cords.
folds=[
 ('FrontSweep',[(-.05,-.27,.24),(-.28,-.35,.68),(-.64,-.20,1.12),(-.61,-.06,1.57),(-.21,-.12,2.05),(.23,-.07,2.52)],[.16,.18,.165,.13,.10,.025]),
 ('FrontRise',[(.16,-.26,.31),(-.11,-.40,.70),(-.34,-.30,1.14),(-.25,-.18,1.58),(.06,-.12,2.06),(.36,.01,2.60)],[.18,.175,.14,.13,.09,.02]),
 ('RearSweep',[(-.38,.17,.30),(-.15,.35,.77),(-.37,.37,1.20),(-.58,.25,1.57),(-.15,.30,2.02),(.31,.20,2.56)],[.16,.15,.145,.13,.10,.02])]
fold_col=bpy.data.collections.new('Buttress_Folds');source.children.link(fold_col)
for name,p,r in folds:tube('SRC_Fold_'+name,[[x*.96,y,z] for x,y,z in p],r,fold_col,'buttress',False)

copies=[]
for ob in parts:
    cp=ob.copy();cp.data=ob.data.copy();wood_col.objects.link(cp);copies.append(cp)
bpy.ops.object.select_all(action='DESELECT')
for ob in copies:ob.select_set(True)
bpy.context.view_layer.objects.active=copies[0];bpy.ops.object.join()
wood=bpy.context.object;wood.name='SM_Tree02_Trunk'
mod=wood.modifiers.new('Continuous_wood','REMESH');mod.mode='VOXEL';mod.voxel_size=.019
bpy.ops.object.modifier_apply(modifier=mod.name)
mod=wood.modifiers.new('Soften_growth_junctions','SMOOTH');mod.factor=.46;mod.iterations=3
bpy.ops.object.modifier_apply(modifier=mod.name)
# Relax only the central junction zone where several broad folds meet.
vg=wood.vertex_groups.new(name='JunctionRelax')
for v in wood.data.vertices:
    w=max(0,1-abs(v.co.z-2.05)/.70)
    if w>0:vg.add([v.index],w,'REPLACE')
mod=wood.modifiers.new('Relax_central_fold_junctions','SMOOTH');mod.factor=.55;mod.iterations=6;mod.vertex_group=vg.name
bpy.ops.object.modifier_apply(modifier=mod.name)
wood.data.calc_loop_triangles()
mod=wood.modifiers.new('Controlled_density','DECIMATE');mod.ratio=min(1,26000/len(wood.data.loop_triangles))
bpy.ops.object.modifier_apply(modifier=mod.name)
for p in wood.data.polygons:p.use_smooth=True
source.hide_render=True;source.hide_viewport=True

# Directional UV: contiguous face regions and continuous per-vertex frames.
segments=[]
for ps,rr,frames,name in paths:
    distance=0
    for i in range(len(ps)-1):
        vec=ps[i+1]-ps[i];length=vec.length
        if length<1e-6:continue
        segments.append((ps[i],vec/length,length,rr[i],rr[i+1],frames[i],distance,name,max(1,round(math.tau*max(rr)/1.25))))
        distance+=length
starts=np.array([list(s[0]) for s in segments]);axes=np.array([list(s[1]) for s in segments]);lengths=np.array([s[2] for s in segments]);r0=np.array([s[3] for s in segments]);r1=np.array([s[4] for s in segments])
uv=wood.data.uv_layers.new(name='UV0_Growth')
path_names=list(dict.fromkeys(s[7] for s in segments))
segment_path=np.array([path_names.index(s[7]) for s in segments])
owners=[]
for face in wood.data.polygons:
    center=sum((wood.data.vertices[v].co for v in face.vertices),Vector())/len(face.vertices)
    q=np.array(center)-starts;raw=np.sum(q*axes,axis=1);t=np.clip(raw,0,lengths)
    distance=np.linalg.norm(q-axes*t[:,None],axis=1);rad=r0+(r1-r0)*t/lengths
    idx=int(np.argmin(distance/(rad+.04)+np.abs(raw-t)*2.5))
    owners.append(int(segment_path[idx]))
# Remove one-face ownership islands without changing the geometry.
edge_faces={}
for face in wood.data.polygons:
    for edge in face.edge_keys:edge_faces.setdefault(tuple(sorted(edge)),[]).append(face.index)
neighbors=[set() for f in wood.data.polygons]
for fs in edge_faces.values():
    for f in fs:neighbors[f].update(set(fs)-{f})
for iteration in range(5):
    revised=list(owners)
    for i,ns in enumerate(neighbors):
        votes={}
        for nidx in ns:votes[owners[nidx]]=votes.get(owners[nidx],0)+1
        if votes:
            best=max(votes,key=votes.get)
            if votes[best]>=2 and votes.get(owners[i],0)==0:revised[i]=best
    owners=revised
cache={}
path_segments=[np.where(segment_path==i)[0] for i in range(len(path_names))]
for face in wood.data.polygons:
    pid=owners[face.index];indices=path_segments[pid];coords=[]
    for li in face.loop_indices:
        vid=wood.data.loops[li].vertex_index;key=(pid,vid)
        if key not in cache:
            point=wood.data.vertices[vid].co
            q=np.array(point)-starts[indices];raw=np.sum(q*axes[indices],axis=1);t=np.clip(raw,0,lengths[indices])
            score=np.sum((q-axes[indices]*t[:,None])**2,axis=1)
            local=int(np.argmin(score));idx=int(indices[local])
            start,axis,length,ra,rb,(side,other),dist,name,repeats=segments[idx]
            f=float(t[local]/length)
            # Interpolate transported frame so adjacent tube samples share the same UV field.
            if idx+1<len(segments) and segment_path[idx+1]==pid:
                side=side.lerp(segments[idx+1][5][0],f).normalized()
                other=other.lerp(segments[idx+1][5][1],f).normalized()
            radial=point-(start+axis*float(t[local]))
            a=math.atan2(radial.dot(other),radial.dot(side))
            cache[key]=(a/math.tau*repeats,(dist+float(raw[local]))/1.25,repeats)
        coords.append((li,*cache[key]))
    repeat=coords[0][3]
    seam=max(c[1] for c in coords)-min(c[1] for c in coords)>repeat*.5
    for li,u,v,rep in coords:
        if seam and u<0:u+=rep
        uv.data[li].uv=(u,v)
uv.active_render=True

bark=bpy.data.materials.new('M_Tree02_Bark');bark.use_nodes=True
n=bark.node_tree.nodes;l=bark.node_tree.links;bs=n.get('Principled BSDF')
bs.inputs['Specular IOR Level'].default_value=.18
tex={}
for suffix in ['BaseColor','Normal','Roughness','AO','Height','DetailNormal','DetailRoughness']:
    im=bpy.data.images.load(str(PROJECT/'Mat/Tree02_Bark'/('Tree02_Bark_'+suffix+'.png')),check_existing=True)
    im.colorspace_settings.name='sRGB' if suffix=='BaseColor' else 'Non-Color';im.pack()
    node=n.new('ShaderNodeTexImage');node.image=im;node.label=suffix;node.location=(-900,-len(tex)*260);tex[suffix]=node
l.new(tex['BaseColor'].outputs['Color'],bs.inputs['Base Color'])
l.new(tex['Roughness'].outputs['Color'],bs.inputs['Roughness'])
normal=n.new('ShaderNodeNormalMap');normal.inputs['Strength'].default_value=.20
l.new(tex['Normal'].outputs['Color'],normal.inputs['Color']);l.new(normal.outputs['Normal'],bs.inputs['Normal'])
for suffix in ['AO','Height','DetailNormal','DetailRoughness']:
    tex[suffix].label=suffix+' | loaded, disabled for initial material test'
wood.data.materials.clear();wood.data.materials.append(bark)
wood['stage']='Stage 2 wood shape + initial directional UV/bark test; branch junction UV still needs refinement.'

# Procedural UV checker is diagnostic only, never exported as an asset texture.
checker=bpy.data.materials.new('QA_UV_Checker');checker.use_nodes=True
cn=checker.node_tree.nodes;cl=checker.node_tree.links
uvnode=cn.new('ShaderNodeTexCoord');chk=cn.new('ShaderNodeTexChecker');chk.inputs['Scale'].default_value=8
chk.inputs['Color1'].default_value=(.05,.13,.16,1);chk.inputs['Color2'].default_value=(.7,.78,.71,1)
cl.new(uvnode.outputs['UV'],chk.inputs['Vector']);cl.new(chk.outputs['Color'],cn.get('Principled BSDF').inputs['Base Color'])

def camera(name,pos,target,size):
    data=bpy.data.cameras.new('CAM_'+name);data.type='ORTHO';data.ortho_scale=size
    ob=bpy.data.objects.new('CAM_'+name,data);studio.objects.link(ob);ob.location=pos
    ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler();return ob
camera('Roots',(3,-9,3.0),(.12,-.05,.86),2.75)
camera('WoodClay',(4,-14,6),(.2,0,2.25),5.6)
camera('RootsClay',(3,-9,3.0),(.12,-.05,.86),2.75)
camera('UV_Check',(4,-14,6),(.2,0,2.25),5.6)
scene.camera=bpy.data.objects['CAM_Perspective'];scene.cycles.samples=32
scene['status']='Tree02 stage 2: wood refinement with initial bark UV test; crown remains stage-1 proxies.'
scene['user_scope']='Continue next part: trunk and roots. No foliage expansion.'
active(wood)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Tree02_Wood.blend'))

bm=bmesh.new();bm.from_mesh(wood.data)
nonmanifold=sum(not e.is_manifold for e in bm.edges)
pending=set(bm.verts);components=[]
while pending:
    stack=[pending.pop()];count=0
    while stack:
        v=stack.pop();count+=1
        for e in v.link_edges:
            other=e.other_vert(v)
            if other in pending:pending.remove(other);stack.append(other)
    components.append(count)
bm.free()
uv_values=np.array([list(v.uv) for v in uv.data])
manifest={'stage':2,'revision':args.revision,'base_file':str(BASE),'base_sha256':base_hash,'wood_triangles':sum(len(p.vertices)-2 for p in wood.data.polygons),'nonmanifold_edges':nonmanifold,'connected_component_vertices':components,'uv_finite':bool(np.isfinite(uv_values).all()),'uv_name':uv.name,'root_count':len(root_col.objects),'fold_count':len(fold_col.objects),'canopy_unchanged':fingerprint(canopy.objects)==canopy_before,'stones_unchanged':fingerprint(stones.objects)==stones_before,'textures_loaded':list(tex),'textures_enabled':['BaseColor','Roughness','Normal strength 0.20'],'uv_status':'Initial along-growth mapping; junction seams not final','views':args.views.split(',')}
(QA/'wood_report.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
assert manifest['canopy_unchanged'] and manifest['stones_unchanged'] and manifest['uv_finite']
assert nonmanifold==0 and len(components)==1
print('WOOD_SAVED',json.dumps(manifest),flush=True)
for name in args.views.split(','):
    scene.camera=bpy.data.objects['CAM_'+name]
    bpy.data.objects['PREVIEW_Floor'].hide_render=name in ['Top','Bottom']
    canopy.hide_render=name in ['WoodClay','RootsClay','Wood','Roots','UV_Check']
    wood.data.materials[0]=clay if name.endswith('Clay') else (checker if name=='UV_Check' else bark)
    scene.render.filepath=str(RENDERS/(name+'.png'))
    bpy.ops.render.render(write_still=True);print('RENDER_DONE',name,flush=True)
assert hashlib.sha256(BASE.read_bytes()).hexdigest()==base_hash
print('BASE_UNCHANGED',flush=True)
