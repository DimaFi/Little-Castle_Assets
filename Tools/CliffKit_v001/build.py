"""Authored CliffKit: metre units, Blender Z-up, Unity +Z into high ground.
Run Blender -b --python Tools/CliffKit_v001/build.py. No Unity runtime code.
Prototype equations/materials retained separately; this recipe fixes their mesh contract.
"""
import bpy, bmesh, math, json, random, sys, importlib.util, hashlib
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'Source/Environment/CliffKit/v001'
spec=importlib.util.spec_from_file_location('prototype',ROOT/'Tools/CliffKit_Prototype_v001/build_cliff_kit.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
SEED=20261009
ARCHETYPES=p.ARCHETYPES

def xyz(v): return (v[0],-v[2],v[1])
def unity(v): return (v[0],v[2],-v[1])

def make_mesh(name,vertices,faces,indices,materials):
    mesh=bpy.data.meshes.new(name);mesh.from_pydata([xyz(v) for v in vertices],[],faces);mesh.update()
    ob=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(ob)
    for m in materials:mesh.materials.append(m)
    bm=bmesh.new();bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free();mesh.update()
    uv=mesh.uv_layers.new(name='UVMap')
    for face,mi in zip(mesh.polygons,indices):
        face.material_index=mi
        face.use_smooth=(mi==1)
        n=face.normal; axis=max(range(3),key=lambda i:abs(n[i]))
        for li in face.loop_indices:
            x,y,z=unity(mesh.vertices[mesh.loops[li].vertex_index].co)
            # Dominant-axis planar UVs: sides never collapse; stratification stays horizontal.
            u,v=(z,y) if axis==0 else ((x,y) if axis==1 else (x,z))
            uv.data[li].uv=(u/6,v/6)
    return ob

def cliff(cfg,lod):
    nx,nv,nc=[(32,8,4),(16,4,2),(16,2,1)][lod]
    w,h,d=cfg['width'],cfg['height'],cfg['depth'];profile=cfg['profile']
    phase=random.Random(cfg['id']).uniform(0,6)
    rng=random.Random(cfg['id']+':buttresses')
    widths=[rng.uniform(.72,1.34) for _ in range(8)]
    cuts=[0]
    for size in widths:cuts.append(cuts[-1]+size/sum(widths))
    tops=[0]+[rng.uniform(-.75,.8) for _ in range(7)]+[0]
    shoulders=[rng.uniform(.65,1.35) for _ in range(8)]
    verts=[];faces=[];mi=[]
    def add(v):verts.append(v);return len(verts)-1
    def quad(a,b,c,e,m=0):faces.extend([(a,b,c),(a,c,e)]);mi.extend([m,m])
    def section(i):
        u=i/nx;x=(u-.5)*w;fade=math.sin(math.pi*u)**2
        # Broad buttresses with narrow recessed joints, no random per-LOD shape noise.
        f=(i/(nx/8))%1
        if lod==0: f=[0,.12,.76,.94][i%4]
        else: f=[0,.76][i%2]
        bay=min(7,math.floor(i/(nx/8)))
        u=cuts[bay]+f*(cuts[bay+1]-cuts[bay]) if i<nx else 1
        x=(u-.5)*w
        u=x/w+.5;fade=math.sin(math.pi*u)**2
        crest=h+tops[bay]*(1-f)+tops[bay+1]*f if i<nx else h
        crest+=fade*.12*math.sin(35*u+phase)
        if profile=='end_left':crest*=.12+.88*min(1,u/.34)
        if profile=='end_right':crest*=.12+.88*min(1,(1-u)/.34)
        bend=(-2 if profile=='convex' else 2 if profile=='concave' else 0)*math.sin(math.pi*u)
        return x,u,fade,crest,bend
    front=[]
    levels=[[0,.13,.36,.40,.63,.68,.92,.97,1],[0,.36,.63,.97,1],[0,.97,1]][lod]
    for j in range(nv+1):
        t=levels[j];row=[]
        for i in range(nx+1):
            x,u,fade,crest,bend=section(i)
            bay=min(7,math.floor(i/(nx/8)));fraction=[0,.12,.76,.94][i%4] if lod==0 else [0,.76][i%2]
            bulge=math.sin(math.pi*fraction)**.4 if fraction>0 else 0
            # A broad shoulder, two weathered shelves, and a recessed vertical joint.
            z=bend-.35+.35*t-fade*(shoulders[bay]*bulge*(.58+.42*math.sin(math.pi*t))+.24*math.sin(9*t+phase+bay))
            x+=fade*.18*math.sin(math.pi*t)*math.sin(phase+bay*2)
            y=-.45+(crest+.45)*t+fade*.19*math.sin(math.pi*t)*math.sin(bay*2+phase+4*t)
            if profile=='terrace':z-=fade*.30*math.sin(t*math.pi*4)**2
            row.append(add((x,y,z)))
        front.append(row)
    for j in range(nv):
        for i in range(nx):quad(front[j][i],front[j][i+1],front[j+1][i+1],front[j+1][i],1 if j==nv-1 else 0)
    cap=[front[-1]]
    for j in range(1,nc+1):
        t=j/nc;row=[]
        for i in range(nx+1):
            x,u,fade,crest,bend=section(i);v=verts[front[-1][i]]
            target=crest if profile.startswith('end') else h
            row.append(add((x,crest*(1-t)+target*t+.05*fade*math.sin(math.pi*t),v[2]*(1-t)+(bend+d)*t)))
        cap.append(row)
    for j in range(nc):
        for i in range(nx):quad(cap[j][i],cap[j][i+1],cap[j+1][i+1],cap[j+1][i],1)
    # Shared indices along every boundary, closed bottom and back; watertight even end modules.
    bottom=[]
    for i in range(nx+1):
        v=verts[cap[-1][i]];bottom.append(add((v[0],-.45,v[2])))
    for i in range(nx):
        quad(cap[-1][i],bottom[i],bottom[i+1],cap[-1][i+1])
        quad(front[0][i],bottom[i],bottom[i+1],front[0][i+1])
    for i in (0,nx):
        loop=[front[j][i] for j in range(nv+1)]+[cap[j][i] for j in range(1,nc+1)]+[bottom[i]]
        center=add(tuple(sum(verts[q][k] for q in loop)/len(loop) for k in range(3)))
        for j,a in enumerate(loop):faces.append((center,a,loop[(j+1)%len(loop)]));mi.append(0)
    return verts,faces,mi

def rock(cfg,lod):
    # Nested angular sampling; each LOD preserves the same characteristic shoulders.
    n=[24,12,8][lod];w,h,d=cfg['width'],cfg['height'],cfg['depth']
    phase=random.Random(cfg['id']).uniform(0,6)
    v=[];f=[];mi=[]
    for t,r in [(-.18,.76),(.19,1),(.65,.88),(.93,.48)]:
        for i in range(n):
            a=i/n*math.tau;rad=r*(1+.12*math.sin(3*a+phase)+.06*math.cos(5*a-phase))
            y=h*(t+.085*math.sin(2*a+phase)*max(0,t))
            v.append((math.cos(a)*w*.5*rad+.12*w*t,y,math.sin(a)*d*.5*rad))
    for j in range(3):
        for i in range(n):
            a=j*n+i;b=j*n+(i+1)%n;c=b+n;e=a+n
            f.extend([(a,b,c),(a,c,e)]);mi.extend([0,0])
    for ring,y in [(0,-.18),(3,1)]:
        center=len(v);v.append((.1*w*y,h*y,0))
        for i in range(n):f.append((center,ring*n+i,ring*n+(i+1)%n));mi.append(0)
    return v,f,mi

def ramp(cfg,lod):
    # Continuous clear 64% corridor, deterministic shoulders, buried toe/skirt.
    nx,nz=[(8,24),(4,12),(4,6)][lod];w,h,length=cfg['width'],cfg['height'],cfg['depth']
    v=[];f=[];mi=[]
    for j in range(nz+1):
        t=j/nz
        for i in range(nx+1):
            u=i/nx;x=(u-.5)*w;edge=max(0,(abs(u-.5)-.25)*4)
            x+=edge*.34*math.sin(math.pi*t)*math.sin(17*t+u*3)
            y=h*t+.42*edge*math.sin(math.pi*t)*(1+.22*math.sin(8*t))
            v.append((x,y,t*length))
    for j in range(nz):
        for i in range(nx):
            a=j*(nx+1)+i;b=a+1;c=b+nx+1;e=a+nx+1
            f.extend([(a,b,c),(a,c,e)]);mi.extend([1 if .18<(i+.5)/nx<.82 else 0]*2)
    boundary=list(range(nx+1))+[j*(nx+1)+nx for j in range(1,nz+1)]+[nz*(nx+1)+i for i in range(nx-1,-1,-1)]+[j*(nx+1) for j in range(nz-1,0,-1)]
    low=[]
    for q in boundary:
        x,y,z=v[q];low.append(len(v));v.append((x,-.45,z))
    for i,a in enumerate(boundary):
        k=(i+1)%len(boundary);f.extend([(a,boundary[k],low[k]),(a,low[k],low[i])]);mi.extend([0,0])
    c=len(v);v.append((0,-.45,length/2))
    for i,a in enumerate(low):f.append((c,a,low[(i+1)%len(low)]));mi.append(0)
    return v,f,mi

def export(objects,path):
    bpy.ops.object.select_all(action='DESELECT')
    for ob in objects:ob.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
    bpy.ops.export_scene.fbx(filepath=str(path),use_selection=True,object_types={'MESH','EMPTY'},
        axis_forward='-Z',axis_up='Y',apply_unit_scale=True,bake_space_transform=False,
        mesh_smooth_type='FACE',add_leaf_bones=False,path_mode='STRIP',use_custom_props=True)

def main():
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'Meshes').mkdir(exist_ok=True)
    p.reset_scene();bpy.context.scene.render.engine='CYCLES'
    mats=[p.make_material('RockA',OUT/'Textures/Rock_Limestone_A',False),p.make_material('RockB',OUT/'Textures/Rock_Limestone_B',False),p.make_material('GrassCap',OUT/'Textures/GrassCap_A',False)]
    for m in mats:m['PROTOTYPE_ONLY']=False
    # Stone is opaque solid ground; cap is rigid ground coverage, never wind foliage.
    catalog=[]
    for cfg in ARCHETYPES:
        aset=[];entry=dict(cfg);entry['archetypeId']='cliffkit_'+cfg['id'].lower()
        for lod in range(3):
            data={'cliff':cliff,'rock':rock,'ramp':ramp}[cfg['kind']](cfg,lod)
            ob=make_mesh(cfg['id']+'_LOD'+str(lod),*data,[mats[1] if cfg['profile']=='boulder' else mats[0]]+([mats[2]] if cfg['kind']!='rock' else []))
            ob['archetypeId']=entry['archetypeId'];ob['LOD']=lod
            aset.append(ob)
        sockets=[]
        if cfg['kind']=='cliff':
            for name,x in [('Socket_Left',-cfg['width']/2),('Socket_Right',cfg['width']/2)]:
                ob=bpy.data.objects.new(name,None);bpy.context.collection.objects.link(ob);ob.location=xyz((x,0,0));sockets.append(ob)
        elif cfg['kind']=='ramp':
            for name,pos in [('Socket_Entry',(0,0,0)),('Socket_Exit',(0,cfg['height'],cfg['depth']))]:
                ob=bpy.data.objects.new(name,None);bpy.context.collection.objects.link(ob);ob.location=xyz(pos);sockets.append(ob)
        for lod,ob in enumerate(aset):export([ob]+sockets,OUT/'Meshes'/f'{ob.name}.fbx')
        entry.update(lod_triangle_counts=[len(o.data.polygons) for o in aset],lod_fbx=[f'Meshes/{o.name}.fbx' for o in aset],pivot='toe centre; metres; Unity Y-up; +Z uphill',render_only_not_navigation=True,colliders='none; terrain owns collision',clear_walk_width_m=cfg['width']*.5 if cfg['kind']=='ramp' else 0,nominal_grade_degrees=math.degrees(math.atan2(cfg['height'],cfg['depth'])) if cfg['kind']=='ramp' else 0)
        catalog.append(entry)
        for ob in sockets:bpy.data.objects.remove(ob,do_unlink=True)
        for lod,ob in enumerate(aset):ob.hide_set(lod!=0);ob.hide_render=lod!=0
    # Move display gallery AFTER export so local pivots in FBX stay at origin.
    for idx,cfg in enumerate(ARCHETYPES):
        for lod in range(3):bpy.data.objects[cfg['id']+'_LOD'+str(lod)].location=xyz(((idx%4)*25,0,(idx//4)*38))
    bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'CliffKit.blend'))
    (OUT/'ASSET_CATALOG.json').write_text(json.dumps(dict(schema='cliffkit-v001',seed=SEED,blender=bpy.app.version_string,unit='m',source_basis='Blender Z-up',unity_basis='Y-up +Z uphill',status='ART_CANDIDATE_UNITY_ACCEPTANCE_REQUIRED',assets=catalog),indent=2)+'\n',encoding='utf-8')
    print('CLIFFKIT_BUILT',len(catalog),'assets / 42 FBX')

if __name__=='__main__':main()
