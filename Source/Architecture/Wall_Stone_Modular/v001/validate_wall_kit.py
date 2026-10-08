"""Blender background QA: binary FBX axes, transforms, names, UVs and readback.
Does not modify exported models. Produces QA/export_validation.json.
"""
import bpy, sys, math, json, hashlib, importlib.util
from pathlib import Path
from io_scene_fbx import parse_fbx
from mathutils import Matrix, Vector
from mathutils.kdtree import KDTree

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('wallbuild',HERE/'build_wall_kit.py')
build=importlib.util.module_from_spec(spec);spec.loader.exec_module(build)
EXPECTED=[(.6,1.4,2),(.6,1.4,1),(.7,1.6,.7),(.6,1.4,.6),(.36,.55,None),(.42,.065,.047)]
SOURCE_POINTS={}

def props(e):
    return {p.props[0].decode():list(p.props[4:]) for s in e.elems if s.id==b'Properties70' for p in s.elems}

def close(a,b,eps=1e-5):
    assert len(a)==len(b) and all(abs(x-y)<eps for x,y in zip(a,b)),(a,b)

def validate_fbx(path,index):
    root,ver=parse_fbx.parse(str(path))
    glob=props(next(e for e in root.elems if e.id==b'GlobalSettings'))
    assert glob['UpAxis']==[1],glob
    close(glob['UnitScaleFactor'],[100.0]) # FBX cm-per-unit; 100 means authored metres.
    obs=next(e for e in root.elems if e.id==b'Objects')
    models={e.props[1].split(b'\x00')[0].decode():e for e in obs.elems if e.id==b'Model'}
    model_names={e.props[0]:name for name,e in models.items()}
    connections=next(e for e in root.elems if e.id==b'Connections')
    geometry_owner={e.props[1]:model_names[e.props[2]] for e in connections.elems
                    if len(e.props)>=3 and e.props[0]==b'OO' and e.props[2] in model_names}
    assert set(models)==({path.stem}|{path.stem+'_LOD'+str(i) for i in range(3)}|
        ({'UCX_'+path.stem} if index<4 else set())|
        ({'BannerAnchor_XPlus','BannerAnchor_XMinus'} if index in [0,2] else set())),list(models)
    for name,e in models.items():
        p=props(e)
        close(p.get('Lcl Scaling',[1,1,1]),[1,1,1])
        if name.startswith('BannerAnchor'):
            sign=1 if name.endswith('XPlus') else -1
            x,y=(.31,1.18) if index==0 else (.36,1.38)
            close(p.get('Lcl Translation',[0,0,0]),[sign*x,y,0])
            close(p.get('Lcl Rotation',[0,0,0]),[0,sign*90,0])
        else:
            close(p.get('Lcl Translation',[0,0,0]),[0,0,0])
            close(p.get('Lcl Rotation',[0,0,0]),[0,0,0])
    geometry=[]
    for e in obs.elems:
        if e.id!=b'Geometry':continue
        name=e.props[1].split(b'\x00')[0].decode()
        vs=list(next(p.props[0] for p in e.elems if p.id==b'Vertices'))
        owner=geometry_owner[e.props[0]]
        if '_LOD' in owner:
            source=SOURCE_POINTS[owner];tree=KDTree(len(source))
            for i,p in enumerate(source):tree.insert(p,i)
            tree.balance()
            assert all(tree.find(Vector(vs[i:i+3]))[2]<2e-5 for i in range(0,len(vs),3)),(owner,'FBX differs from source geometry')
        assert all(math.isfinite(v) for v in vs)
        lo=[min(vs[i::3]) for i in range(3)];hi=[max(vs[i::3]) for i in range(3)]
        size=[hi[i]-lo[i] for i in range(3)]
        if not name.startswith('UCX_'):
            for i,want in enumerate(EXPECTED[index]):
                if want is not None:close([size[i]],[want],.0001)
            if index<4:close([lo[1]],[0])
            if index==4:
                close([hi[1]],[0]);assert lo[2]>=-.001 and hi[2]<=.031
        geometry.append({'name':name,'bounds_unity':{'min':lo,'max':hi,'size':size}})
    # Ordinary re-import, then compare WORLD vertices with the source Z-up space.
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(path),use_image_search=False)
    lods=[]
    for ob in bpy.context.scene.objects:
        if ob.type!='MESH' or '_LOD' not in ob.name:continue
        ob.data.calc_loop_triangles();assert ob.data.uv_layers
        me=ob.data;uv=me.uv_layers.active.data
        for tri in me.loop_triangles:
            a,b,c=[me.vertices[i].co for i in tri.vertices]
            assert (b-a).cross(c-a).length>1e-10,(ob.name,'degenerate face')
            a,b,c=[uv[i].uv for i in tri.loops]
            assert abs((b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x))>1e-12,(ob.name,'degenerate UV')
        points=[build.U(ob.matrix_world@v.co) for v in me.vertices]
        size=[max(p[i] for p in points)-min(p[i] for p in points) for i in range(3)]
        for i,want in enumerate(EXPECTED[index]):
            if want is not None:close([size[i]],[want],.0001)
        if index==4:
            for axis in [0,1]:close([min(p.uv[axis] for p in uv),max(p.uv[axis] for p in uv)],[0,1])
        assert len(me.materials)==1
        lods.append({'name':ob.name,'triangles':len(me.loop_triangles),'material':me.materials[0].name})
    lods.sort(key=lambda row:row['name'])
    assert len(lods)==3 and all(lods[i]['triangles']>lods[i+1]['triangles'] for i in [0,1]),lods
    return {'file':path.name,'status':'PASS','fbx_version':ver,'Y_up':True,'metre_units':True,
            'identity_roots':True,'locators_verified':index in [0,2],
            'raw_geometry':geometry,'roundtrip_lods':lods}

def footprints_overlap(ca,yawa,ha,cb,yawb,hb):
    def corners(c,y,h):
        a=math.radians(y);right=Vector((math.cos(a),-math.sin(a)));fwd=Vector((math.sin(a),math.cos(a)))
        return [Vector(c)+right*x*h[0]+fwd*z*h[1] for x,z in [(-1,-1),(1,-1),(1,1),(-1,1)]]
    a=corners(ca,yawa,ha);b=corners(cb,yawb,hb)
    for p in [a,b]:
        for i in range(2):
            edge=p[i+1]-p[i];axis=Vector((-edge.y,edge.x)).normalized()
            pa=[q.dot(axis) for q in a];pb=[q.dot(axis) for q in b]
            if min(max(pa),max(pb))<=max(min(pa),min(pb)):return False
    return True

if __name__=='__main__':
    result={'status':'PASS','unity_playmode_tested':False,'exports':[]}
    source_path=HERE/'Wall_Stone_Modular.blend'
    bpy.ops.wm.open_mainfile(filepath=str(source_path))
    for name in build.NAMES:
        for lod in range(3):
            ob=bpy.data.objects[name+'_LOD'+str(lod)]
            SOURCE_POINTS[ob.name]=[Vector(build.U(v.co)) for v in ob.data.vertices]
    result['source_sha256']=hashlib.sha256(source_path.read_bytes()).hexdigest()
    for i,name in enumerate(build.NAMES):result['exports'].append(validate_fbx(HERE/'Meshes'/f'{name}.fbx',i))
    # Rigid five-degree arc, straight 2m/1m transition and pillar-covered 90-degree corner.
    centers=[];start=Vector((0,0))
    for yaw in range(0,26,5):
        f=Vector((math.sin(math.radians(yaw)),math.cos(math.radians(yaw))))
        center=start+f*.96;centers.append((center,yaw));start=center+f*.96
    assert all(footprints_overlap(a,ya,(.3,1),b,yb,(.3,1)) for (a,ya),(b,yb) in zip(centers,centers[1:]))
    assert footprints_overlap((0,0),0,(.3,1),(0,1.42),0,(.3,.5))
    assert footprints_overlap((0,0),0,(.35,.35),(0,1.27),0,(.3,1))
    assert footprints_overlap((0,0),0,(.35,.35),(1.27,0),90,(.3,1))
    result['assembly_footprints']='PASS: straight, 2m-to-1m, 5deg arc, 90deg pillar junction'
    # Preserve and verify all user maps without editing their pixels.
    original=build.WORKSPACE/'CozySettlement/Mat/StoneWall_A_Unity'
    result['textures']=[]
    for p in sorted(original.glob('*.png')):
        q=HERE/'Textures'/p.name
        assert hashlib.sha256(p.read_bytes()).digest()==hashlib.sha256(q.read_bytes()).digest()
        result['textures'].append({'file':p.name,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()})
    bpy.ops.wm.open_mainfile(filepath=str(HERE/'Wall_Stone_Modular.blend'))
    assert all(name in bpy.data.objects for name in build.NAMES)
    assert bpy.context.scene.camera is not None
    required=['StoneWall_A_BaseColor_2048.png','StoneWall_A_Normal_2048.png','StoneWall_A_Roughness_2048.png']
    assert all(bpy.data.images.get(name) and bpy.data.images[name].packed_file for name in required)
    result['editable_source_reopen']='PASS; six source roots, studio camera, packed texture inputs'
    (HERE/'QA/export_validation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print('WALL_EXPORT_VALIDATION_PASS',flush=True)
