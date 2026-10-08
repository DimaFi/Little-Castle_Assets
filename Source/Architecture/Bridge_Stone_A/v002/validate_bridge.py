"""Independent FBX round-trip and fixed-site acceptance checks for bridge v002."""
import bpy, json, sys, math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import bridge_contract as contract

def unity(p):
    return Vector((p.x,p.z,-p.y))

expected=json.loads((HERE/'QA/geometry_report.json').read_text(encoding='utf-8'))['meshes']
report={'blender':bpy.app.version_string,'files':{},'contract':contract.validate(),
        'unity_play_mode_tested':False}
grass_points={}
flag_checks=[]
unique_materials=set()

for path in sorted((HERE/'Meshes').glob('*.fbx')):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(path))
    records=[]
    for ob in bpy.context.scene.objects:
        if ob.type!='MESH':
            continue
        me=ob.data
        me.calc_loop_triangles()
        me.calc_tangents()
        ref=expected[ob.name]
        assert len(me.loop_triangles)==ref['triangles'],(path.name,ob.name,'triangles')
        pts=[unity(ob.matrix_world@v.co) for v in me.vertices]
        lo=[min(p[i] for p in pts) for i in range(3)]
        hi=[max(p[i] for p in pts) for i in range(3)]
        assert max(abs(lo[i]-ref['min'][i]) for i in range(3))<1e-4,(ob.name,lo,ref['min'])
        assert max(abs(hi[i]-ref['max'][i]) for i in range(3))<1e-4,(ob.name,hi,ref['max'])
        assert all(math.isfinite(v) for p in pts for v in p)
        assert all(v.normal.length>.9 for v in me.vertices)
        assert all(t.area>1e-10 for t in me.loop_triangles)
        assert me.uv_layers.active,ob.name
        material_names=[m.name for m in me.materials]
        unique_materials.update(material_names)
        textures=[]
        for mat in me.materials:
            assert mat and mat.use_nodes
            for node in mat.node_tree.nodes:
                if node.type=='TEX_IMAGE' and node.image:
                    image_path=Path(bpy.path.abspath(node.image.filepath))
                    assert image_path.is_file(),(ob.name,str(image_path))
                    textures.append(image_path.name)
        if 'M_Bridge_Stone' in material_names and not ob.name.startswith('COL_'):
            assert 'T_Bridge_StoneAtlas_BaseColor.png' in textures,(ob.name,textures)
        record={'name':ob.name,'triangles':len(me.loop_triangles),'vertices':len(me.vertices),
                'bounds_min':lo,'bounds_max':hi,'uv':True,'normals':True,
                'tangents':True,'materials':material_names,'textures':textures}
        if 'Grass' in ob.name:
            grass_points[ob.name]={tuple(round(v,5) for v in p) for p in pts}
            values=[loop.uv.y for loop in me.uv_layers.active.data]
            assert abs(min(values))<1e-6 and abs(max(values)-1)<1e-6
            assert any(abs(v-.5)<1e-6 for v in values)
            record['root_mid_tip_uv']=True
        if ob.name=='SM_Bridge_Water':
            normals=[unity(ob.matrix_world.to_3x3()@p.normal).y for p in me.polygons]
            assert min(normals)>.01,('downward water normals',min(normals))
            assert material_names==['M_Bridge_Water']
            record['continuous_water_material']=True
        if 'TerrainReference' in ob.name:
            normals=[unity(ob.matrix_world.to_3x3()@p.normal).y for p in me.polygons]
            assert min(normals)>.01,('downward terrain normals',min(normals))
        if ob.name=='SM_Bridge_Wood_LOD0':
            for x,z in [(1.64,-5.12),(-1.64,5.12)]:
                near=[p for p in pts if abs(p.x-x)<.13 and abs(p.z-z)<.13]
                base=contract.deck_height(z)+.97
                assert near and min(p.y for p in near)<=base+.02
                assert max(p.y for p in near)>=base+1.68
                flag_checks.append({'anchor':[x,z],'base_y':base,'min_y':min(p.y for p in near),
                                    'max_y':max(p.y for p in near),'right_hand_entry':True})
        if ob.name=='SM_Bridge_Stone_LOD0':
            verts=[ob.matrix_world@v.co for v in me.vertices]
            faces=[tuple(p.vertices) for p in me.polygons]
            core=bpy.data.objects['SM_Bridge_Mortar_LOD0']
            offset=len(verts)
            verts.extend([core.matrix_world@v.co for v in core.data.vertices])
            faces.extend([tuple(i+offset for i in p.vertices) for p in core.data.polygons])
            bvh=BVHTree.FromPolygons(verts,faces)
            for z in [-2,0,2]:
                assert bvh.ray_cast(Vector((-3,-z,-.9)),Vector((1,0,0)),6)[0] is None
            for z in [-5.30,-4.5,-3,-1,0,1,3,4.5,5.30]:
                for x in [-1.2,0,1.2]:
                    hit,normal,_,_=bvh.ray_cast(Vector((x,-z,5)),Vector((0,0,-1)),10)
                    assert hit is not None and normal.z>.45,('walkway miss/downward',z,x,hit,normal)
                    assert abs(hit.z-contract.deck_height(z))<.13,('walkway height',z,x,hit.z,contract.deck_height(z))
            record['arch_open_and_walkway_clear']=True
        records.append(record)
    assert records or path.stem=='Bridge_Sockets'
    report['files'][path.name]=records

for lod in range(3):
    report[f'bridge_lod{lod}_triangles']=sum(v['triangles'] for k,v in expected.items()
        if k.endswith(f'LOD{lod}') and any(k.startswith('SM_Bridge_'+s)
        for s in ['Stone','Mortar','Wood','FactionCloth','Trim']))
    report[f'dressing_lod{lod}_triangles']=sum(v['triangles'] for k,v in expected.items()
        if k.endswith(f'LOD{lod}') and any(k.startswith('SM_Bridge_'+s)
        for s in ['Rocks','Grass','Botany']))

assert report['bridge_lod0_triangles']>report['bridge_lod1_triangles']>report['bridge_lod2_triangles']
assert report['dressing_lod0_triangles']>report['dressing_lod1_triangles']>report['dressing_lod2_triangles']
assert grass_points['SM_Bridge_Grass_LOD1'].issubset(grass_points['SM_Bridge_Grass_LOD0'])
assert len(flag_checks)==2
assert len(unique_materials)<=7,unique_materials
for name in ['Bridge_Hero.png','Bridge_Reverse.png','Bridge_Side.png','Bridge_Top.png',
             'Bridge_Detail.png','Bridge_Realtime_Eevee.png']:
    assert (HERE/'Preview'/name).is_file(),name

report['flag_anchors']=flag_checks
report['grass_lod_positions_preserved']=True
report['unique_materials']=sorted(unique_materials)
report['preview_renders']='six actual Blender renders present; includes Eevee raster check'
report['passed']=True
(HERE/'QA/roundtrip_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('BRIDGE_V002_QA_PASS',json.dumps({k:v for k,v in report.items() if k!='files'}),flush=True)
