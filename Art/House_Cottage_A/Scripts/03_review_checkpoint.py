"""Read saved checkpoint, report measured geometry, render a separate module gallery.
This validates a Blender blockout only, never engine readiness or visual likeness.
"""
from pathlib import Path
import sys, argparse, json, math
sys.path.insert(0,str(Path(__file__).parent))
from geometry import *

ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--revision',required=True);p.add_argument('--module-revision',default='v002')
args=p.parse_args(sys.argv[sys.argv.index('--')+1:])
source=ROOT/'Source/Blockout'/args.revision/'House_Cottage_A_Blockout.blend'
bpy.ops.wm.open_mainfile(filepath=str(source))
root=bpy.data.collections['COL_House_Cottage_A']
objects=[o for o in root.all_objects if o.type=='MESH']
deps=bpy.context.evaluated_depsgraph_get(); bad=[]; bounds=[]; triangles=0
for o in objects:
    ev=o.evaluated_get(deps);me=ev.to_mesh();me.calc_loop_triangles()
    triangles+=len(me.loop_triangles)
    for v in me.vertices:
        if not all(math.isfinite(x) for x in v.co):bad.append({'object':o.name,'issue':'nonfinite vertex'})
        bounds.append(o.matrix_world@v.co)
    degenerate=sum(1 for t in me.loop_triangles if t.area<1e-10)
    if degenerate:bad.append({'object':o.name,'issue':'degenerate triangles','count':degenerate})
    ev.to_mesh_clear()
low=[min(v[i] for v in bounds) for i in range(3)];high=[max(v[i] for v in bounds) for i in range(3)]
materials=sorted({m.name for o in objects for m in o.data.materials if m})
checks={
    'all_vertices_finite_and_triangles_nonzero':not bad,
    'one_grey_material':materials==['M_Blockout_Grey'],
    'nine_review_cameras':len([o for o in bpy.data.objects if o.type=='CAMERA'])==9,
    'house_width_under_8m':high[0]-low[0]<8,
    'chimney_higher_than_ridge':high[2]>6.5,
    'door_height_2_05m':abs(bpy.data.objects['SM_Door_Main_A'].dimensions.z-2.05)<.01,
    'separate_roof_halves':all(n in bpy.data.objects for n in ['SM_Roof_Main_Front_A','SM_Roof_Main_Back_A']),
    'no_image_texture_nodes_on_house':not any(n.type=='TEX_IMAGE' for m in bpy.data.materials if m.name in materials for n in m.node_tree.nodes),
}
report={'source':str(source),'checks':checks,'passed':all(checks.values()),'object_count':len(objects),'evaluated_triangles':triangles,'bounds_min_m':low,'bounds_max_m':high,'materials':materials,'issues':bad,'limits':['No engine import, collision, LOD or UV validation.','Intersections at roof/dormer/chimney are blockout volumes.','Visual likeness requires comparing saved renders to supplied concepts.']}
(ROOT/'QA'/('geometry_review_'+args.revision+'.json')).write_text(json.dumps(report,indent=2),encoding='utf-8')
print('BLOCKOUT_CHECKS',json.dumps(checks),flush=True)
if not report['passed']:raise RuntimeError('Checkpoint geometry checks failed; inspect JSON')

# Save an easy-to-browse gallery without changing canonical module coordinates.
module_dir=ROOT/'Source/Modules'/args.module_revision
preview=module_dir/'Cottage_A_Primitives_Preview.blend'
if preview.exists():
    print('Existing module gallery preserved:',preview)
    sys.exit(0)
bpy.ops.wm.open_mainfile(filepath=str(module_dir/'Cottage_A_Primitives.blend'))
scene=bpy.context.scene;mat=bpy.data.materials['M_Blockout_Grey']
stone=bpy.data.objects['SM_Foundation_Block_A'];beam_o=bpy.data.objects['SM_Beam_Vertical_A'];tile=bpy.data.objects['SM_RoofTile_A']
stone.location=(-.9,0,0);beam_o.location=(0,.12,0);tile.location=(.8,-.15,.06)
st=studio(scene,mat)
cam=camera('CAM_Modules',(4,-7,4),(0,0,1.05),3.65,st);scene.camera=cam
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA'
bpy.ops.wm.save_as_mainfile(filepath=str(preview))
render(scene,cam,ROOT/'Renders/Checkpoint_01'/args.revision/'00_Primitives.png',800)
print('MODULE_GALLERY_SAVED',preview,flush=True)
