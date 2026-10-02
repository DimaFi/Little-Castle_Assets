"""Read saved Tree02 wood, verify it and render additional review cameras.
Run with --factory-startup and -- --revision v004 --views Front,Back,...
"""
import argparse,hashlib,json,sys
from pathlib import Path
import bpy,bmesh
from mathutils import Vector

p=argparse.ArgumentParser();p.add_argument('--revision',default='v004');p.add_argument('--views',default='Front,Back,Left,Right,Top,Bottom,Gameplay')
a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
assert a.revision.isalnum()
root=Path(__file__).resolve().parent
source=root/'Source'/a.revision/'Tree02_Wood.blend'
bpy.ops.wm.open_mainfile(filepath=str(source))
wood=bpy.data.objects['SM_Tree02_Trunk'];scene=bpy.context.scene
assert wood.location.length<1e-6
assert len(wood.data.materials)==1 and wood.data.materials[0].name=='M_Tree02_Bark'
assert len(bpy.data.collections['Roots'].objects)==7
assert len(bpy.data.collections['Canopy_Proxies_NOT_FINAL_LEAVES'].objects)==8
assert len(bpy.data.collections['03_OPTIONAL_STONES_FROM_OAK_KIT'].objects)==2
assert all(im.packed_file or im.source in {'GENERATED','VIEWER'} for im in bpy.data.images)
bm=bmesh.new();bm.from_mesh(wood.data)
bad=sum(not e.is_manifold for e in bm.edges)
degenerate=sum(f.calc_area()<1e-10 for f in bm.faces)
bm.free();assert bad==0 and degenerate==0
project=root.parents[2]
inventory=json.loads((root/'inventory.json').read_text(encoding='utf-8'))
assert all(hashlib.sha256((project/r['path']).read_bytes()).hexdigest()==r['sha256'] for r in inventory['files'])
stage1=json.loads((root/'QA/v002/blockout_report.json').read_text(encoding='utf-8'))
assert hashlib.sha256(Path(stage1['stone_source']).read_bytes()).hexdigest()==stage1['stone_source_sha256']
report=json.loads((root/'QA'/a.revision/'wood_report.json').read_text())
assert hashlib.sha256(Path(report['base_file']).read_bytes()).hexdigest()==report['base_sha256']
for name in a.views.split(','):
    scene.camera=bpy.data.objects['CAM_'+name]
    bpy.data.objects['PREVIEW_Floor'].hide_render=name in ['Top','Bottom']
    scene.render.filepath=str(root/'Renders'/a.revision/(name+'.png'))
    bpy.ops.render.render(write_still=True)
    print('RENDER_DONE',name,flush=True)
report['views']=list(dict.fromkeys(report['views']+a.views.split(',')))
report['reopen_verified']=True
report['degenerate_faces']=degenerate
report['input_assets_unchanged']=True
report['previous_model_unchanged']=True
report['wood_bounds_m']=[list(min((wood.matrix_world@Vector(c))[i] for c in wood.bound_box) for i in range(3)),list(max((wood.matrix_world@Vector(c))[i] for c in wood.bound_box) for i in range(3))]
(root/'QA'/a.revision/'wood_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('SAVED_MODEL_AND_ORIGINALS_VERIFIED',flush=True)
