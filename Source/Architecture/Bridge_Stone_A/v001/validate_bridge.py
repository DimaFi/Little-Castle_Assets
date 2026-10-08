"""Independent FBX round-trip, collision, UV and fixed-site acceptance checks."""
import bpy, json, sys, math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import bridge_contract as c

def unity(p):return Vector((p.x,p.z,-p.y))

expected=json.loads((HERE/'QA/geometry_report.json').read_text())['meshes']
report={'files':{},'contract':c.validate(),'unity_play_mode_tested':False}
grass_points={}
for path in sorted((HERE/'Meshes').glob('*.fbx')):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(path))
    records=[]
    for ob in bpy.context.scene.objects:
        if ob.type!='MESH':continue
        me=ob.data;me.calc_loop_triangles();me.calc_tangents()
        ref=expected[ob.name]
        assert len(me.loop_triangles)==ref['triangles'],(path.name,ob.name,'triangles')
        pts=[unity(ob.matrix_world@v.co) for v in me.vertices]
        lo=[min(p[i] for p in pts) for i in range(3)];hi=[max(p[i] for p in pts) for i in range(3)]
        assert max(abs(lo[i]-ref['min'][i]) for i in range(3))<1e-4,(ob.name,lo,ref['min'])
        assert max(abs(hi[i]-ref['max'][i]) for i in range(3))<1e-4
        assert all(math.isfinite(v) for p in pts for v in p)
        assert all(v.normal.length>.9 for v in me.vertices)
        assert all(t.area>1e-10 for t in me.loop_triangles)
        assert me.uv_layers.active
        paths=[]
        for mat in me.materials:
            for node in mat.node_tree.nodes:
                if node.type=='TEX_IMAGE' and node.image:
                    img=Path(bpy.path.abspath(node.image.filepath))
                    assert img.is_file(),(ob.name,str(img))
                    paths.append(str(img.relative_to(HERE)))
        r=dict(name=ob.name,triangles=len(me.loop_triangles),vertices=len(me.vertices),
               bounds_min=lo,bounds_max=hi,uv=True,normals=True,tangents=True,textures=paths)
        if 'Grass' in ob.name:
            grass_points[ob.name]={tuple(round(v,5) for v in p) for p in pts}
            uv=me.uv_layers.active
            values=[v.uv.y for v in uv.data]
            assert min(values)==0 and max(values)==1
            assert any(abs(v-.5)<1e-6 for v in values)
            r['root_mid_tip_uv']=True
        if 'Water'==ob.name.split('_')[-1] or 'TerrainReference' in ob.name:
            normals=[unity(ob.matrix_world.to_3x3()@p.normal).y for p in me.polygons]
            assert min(normals)>.01,(ob.name,'downward terrain/water normals',min(normals))
            r['upward_normals']=True
        if ob.name=='SM_Bridge_Stone_LOD0':
            verts=[ob.matrix_world@v.co for v in me.vertices]
            faces=[tuple(p.vertices) for p in me.polygons]
            core=bpy.data.objects['SM_Bridge_Mortar_LOD0'];offset=len(verts)
            verts.extend([core.matrix_world@v.co for v in core.data.vertices])
            faces.extend([tuple(i+offset for i in p.vertices) for p in core.data.polygons])
            bvh=BVHTree.FromPolygons(verts,faces)
            # Through the arch, along X at three longitudinal offsets.
            for z in [-2,0,2]:
                hit=bvh.ray_cast(Vector((-3,-z,-.9)),Vector((1,0,0)),6)[0]
                assert hit is None,('blocked arch',z,hit)
            # Paving surface and unobstructed pedestrian corridor.
            heights=[]
            for z in [-5.39,-4.5,-3,-1,0,1,3,4.5,5.39]:
                for x in [-1.2,0,1.2]:
                    hit,normal,_,_=bvh.ray_cast(Vector((x,-z,5)),Vector((0,0,-1)),10)
                    assert hit is not None
                    assert normal.z>.45,('downward paving',z,x,list(normal))
                    assert abs(hit.z-c.deck_height(z))<.13,(z,x,hit.z,c.deck_height(z))
                    heights.append(hit.z)
            r['arch_open_and_walkway_clear']=True
            for sign in [-1,1]:
                hit,normal,_,_=bvh.ray_cast(Vector((sign*3,-4.2,-.4)),Vector((-sign,0,0)),4)
                assert hit is not None and normal.x*sign>.8,('inward spandrel',sign,normal)
        records.append(r)
    assert records or path.stem=='Bridge_Sockets'
    report['files'][path.name]=records
for lod in range(3):
    report[f'bridge_lod{lod}_triangles']=sum(v['triangles'] for k,v in expected.items()
        if k.endswith(f'LOD{lod}') and any(k.startswith('SM_Bridge_'+s) for s in ['Stone','Mortar','Wood','FactionCloth','Trim']))
assert report['bridge_lod0_triangles']>report['bridge_lod1_triangles']>report['bridge_lod2_triangles']
assert grass_points['SM_Bridge_Grass_LOD1'].issubset(grass_points['SM_Bridge_Grass_LOD0']), 'Grass jumps between LODs'
report['grass_lod_positions_preserved']=True
report['passed']=True
(HERE/'QA/roundtrip_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('BRIDGE_QA_PASS',json.dumps({k:v for k,v in report.items() if k!='files'}),flush=True)
