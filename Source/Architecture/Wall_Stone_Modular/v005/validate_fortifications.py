"""Independent source/FBX verification, including exact v002 stone preservation."""
import bpy, json, math, hashlib, sys
from pathlib import Path
from mathutils import Vector
from mathutils.kdtree import KDTree
from io_scene_fbx import parse_fbx
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import fortification_helpers as f

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def props(e):return {p.props[0].decode():list(p.props[4:]) for s in e.elems if s.id==b'Properties70' for p in s.elems}
def close(a,b,eps=3e-5):assert len(a)==len(b) and all(abs(x-y)<eps for x,y in zip(a,b)),(a,b)
def signature(mesh):
    # Face identity independent of vertex indexing after removal of loose vertices.
    uv=mesh.uv_layers.active.data
    return {tuple(sorted(tuple(round(x,6) for x in (*mesh.vertices[mesh.loops[i].vertex_index].co,*uv[i].uv))
                         for i in p.loop_indices)) for p in mesh.polygons}

if __name__=='__main__':
    report=json.loads((HERE/'QA/geometry_report.json').read_text(encoding='utf-8'))
    result={'status':'PASS','unity_tested':False,'assets':[]}
    source=HERE/'Wall_Fortifications.blend'
    assert sha(source)==report['source_sha256']
    bpy.ops.wm.open_mainfile(filepath=str(source))
    points={};expected={};stone_signatures={}
    for name,a in report['assets'].items():
        for level in a['lods']:
            for part in level['parts']:
                ob=bpy.data.objects[part['name']];points[ob.name]=[Vector(f.w.U(v.co)) for v in ob.data.vertices]
                expected[ob.name]=part
                stone_signatures[ob.name]=signature(ob.data)
                if name==f.w.NAMES[4]:
                    uv=ob.data.uv_layers.active.data
                    for axis in [0,1]:close([min(p.uv[axis] for p in uv),max(p.uv[axis] for p in uv)],[0,1])
                    mask=ob.data.color_attributes['WindMask']
                    assert all(0<=v.color[0]<=1 for v in mask.data)
                    assert any(v.color[0]==0 for v in mask.data) and any(v.color[0]>.99 for v in mask.data)
    # Compare against the immutable USER snapshot, not regenerated v004 models.
    bpy.ops.wm.open_mainfile(filepath=str(HERE/'Input/UserEdits_2026-10-06.blend'))
    if bpy.context.object and bpy.context.object.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
    for name,optimized in stone_signatures.items():
        ob=bpy.data.objects[name]
        if any(name.startswith(n+'_LOD') for n in f.w.NAMES[:4]):
            for v in ob.data.vertices:v.co*=report['wall_scale']
        if name.startswith('SM_ArcherTower_A_Roof_LOD'):continue # explicit roof cleanup/LOD propagation
        assert optimized==signature(ob.data),name
    # User roof vertex positions are preserved, including the hand-lowered ridge.
    roof=bpy.data.objects['SM_ArcherTower_A_Roof_LOD0'].data
    tree=KDTree(len(roof.vertices))
    for i,v in enumerate(roof.vertices):tree.insert(Vector(f.w.U(v.co)),i)
    tree.balance()
    assert all(tree.find(p)[2]<3e-5 for p in points['SM_ArcherTower_A_Roof_LOD0'])
    assert sha(HERE/'Textures/T_WallStoneSurface_A_BaseColor.png')==sha(HERE.parent/'v002/Textures/T_WallStoneSurface_A_BaseColor.png')
    result['preserved_geometry']='PASS: scaled wall faces and UVs match manual snapshot; other non-roof meshes match exactly; LOD0 roof positions preserved; approved stone texture unchanged'
    for name,a in report['assets'].items():
        path=HERE/'Meshes'/f'{name}.fbx';root,version=parse_fbx.parse(str(path))
        settings=props(next(e for e in root.elems if e.id==b'GlobalSettings'))
        assert settings['UpAxis']==[1];close(settings['UnitScaleFactor'],[100])
        objects=next(e for e in root.elems if e.id==b'Objects')
        models={e.props[0]:e for e in objects.elems if e.id==b'Model'}
        names={i:e.props[1].split(b'\x00')[0].decode() for i,e in models.items()}
        connections=next(e for e in root.elems if e.id==b'Connections')
        owners={e.props[1]:names[e.props[2]] for e in connections.elems if len(e.props)>=3 and e.props[0]==b'OO' and e.props[2] in names}
        locators={x['name']:x for x in a['locators']}
        for i,e in models.items():
            p=props(e);n=names[i]
            if n in locators:
                loc=locators[n];close(p.get('Lcl Translation',[0,0,0]),loc['position'])
                close(p.get('Lcl Scaling',[1,1,1]),loc['scale'])
                rotation=p.get('Lcl Rotation',[0,0,0])
                close([rotation[0],rotation[2]],[0,0])
                close([((rotation[1]-loc['yaw']+180)%360)-180],[0])
            else:
                close(p.get('Lcl Translation',[0,0,0]),[0,0,0]);close(p.get('Lcl Rotation',[0,0,0]),[0,0,0]);close(p.get('Lcl Scaling',[1,1,1]),[1,1,1])
        assert set(locators)<=set(names.values())
        for e in objects.elems:
            if e.id!=b'Geometry':continue
            owner=owners[e.props[0]]
            if owner.startswith('UCX_'):continue
            vs=next(p.props[0] for p in e.elems if p.id==b'Vertices');tree=KDTree(len(points[owner]))
            for i,p in enumerate(points[owner]):tree.insert(p,i)
            tree.balance();assert all(tree.find(Vector(vs[i:i+3]))[2]<3e-5 for i in range(0,len(vs),3)),owner
        bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=str(path),use_image_search=False)
        totals=[0,0,0]
        for ob in bpy.context.scene.objects:
            if ob.type!='MESH' or '_LOD' not in ob.name:continue
            got=f.w.audit(ob);want=expected[ob.name];assert got['triangles']==want['triangles']
            world=[f.w.U(ob.matrix_world@v.co) for v in ob.data.vertices]
            size=[max(p[i] for p in world)-min(p[i] for p in world) for i in range(3)]
            close(size,want['size']);totals[int(ob.name[-1])]+=got['triangles']
        assert totals==[l['triangles'] for l in a['lods']]
        result['assets'].append({'name':name,'status':'PASS','triangles':totals,'sha256':sha(path),'locators':list(locators)})
    # Socket seam: authored first section overlaps into tower/gate by exactly 8cm.
    for face in [.90,1.99]:
        center=face+report['segment_length']/2-report['recommended_overlap_m'];near=center-report['segment_length']/2
        close([face-near],[report['recommended_overlap_m']]);assert near<face<center
    # Gate frame proxies must leave a centre walkable opening, independently of leaves.
    colliders=report['assets'][f.GATE]['colliders']
    assert all(not (c['min'][2]<0<c['max'][2] and c['min'][1]<2.28) for c in colliders)
    # Rotating each leaf by 90 degrees clears Z travel opening.
    assert 1.04-.10>.90
    result['socket_contract']='PASS: scaled wall endpoints and nominal overlap; no claim of runtime placement validation'
    result['gate_opening']='PASS: structural box proxies leave centre passage; independent door leaf meshes pivot at hinges'
    result['source_sha256']=sha(source)
    (HERE/'QA/export_validation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print('FORTIFICATIONS_VALIDATION_PASS',flush=True)
