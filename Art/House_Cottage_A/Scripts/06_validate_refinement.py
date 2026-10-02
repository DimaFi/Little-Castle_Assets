"""Validate saved v005 roof holes by ray tests and package stone source objects."""
from pathlib import Path
import bpy,json
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Source/Refinement/v005/House_Cottage_A.blend'))
deps=bpy.context.evaluated_depsgraph_get()
def hits(name,x,y):
    o=bpy.data.objects[name].evaluated_get(deps);inv=o.matrix_world.inverted()
    return bool(o.ray_cast(inv@Vector((x,y,10)),(inv.to_3x3()@Vector((0,0,-1))).normalized())[0])
checks={
 'dormer_hole_clear':not hits('SM_Roof_Main_Front_A',.52,-1.8),
 'chimney_hole_clear':not hits('SM_Roof_Main_Back_A',-2.94,.72),
 'front_roof_retained':hits('SM_Roof_Main_Front_A',2,-1.8),
 'back_roof_retained':hits('SM_Roof_Main_Back_A',0,1),
}
file=ROOT/'QA/refinement_v005.json';report=json.loads(file.read_text(encoding='utf-8'))
report['checks'].pop('two_actual_roof_openings',None)
report['checks'].update(checks)
report['passed']=all(report['checks'].values())
file.write_text(json.dumps(report,indent=2),encoding='utf-8')
assert report['passed'],checks
out=ROOT/'Source/Modules/v003';out.mkdir(parents=True,exist_ok=True)
target=out/'Foundation_Stones.blend'
if not target.exists():
    assets={bpy.data.objects['SM_Foundation_Stone_'+c] for c in 'ABC'}
    bpy.data.libraries.write(str(target),assets,fake_user=True)
print('REFINEMENT_CHECKS',checks,'MODULE_LIBRARY',target)
