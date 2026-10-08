"""Read back the saved geometry. Installed triangles, topology, and user-requested clearances."""
import bpy,bmesh,json,math
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(P/'Church_A.blend'))
deps=bpy.context.evaluated_depsgraph_get();issues=[];tris=0;bounds={};counts={}
for o in bpy.context.scene.objects:
 if o.type!='MESH' or any(c.name=='90_STUDIO' for c in o.users_collection):continue
 ev=o.evaluated_get(deps);me=ev.to_mesh();me.calc_loop_triangles();tris+=len(me.loop_triangles)
 bm=bmesh.new();bm.from_mesh(me)
 if any(not e.is_manifold for e in bm.edges):issues.append(o.name+': nonmanifold edge')
 if any(t.area<1e-10 for t in me.loop_triangles):issues.append(o.name+': degenerate triangle')
 pts=[o.matrix_world@v.co for v in me.vertices]
 bounds[o.name]=([min(v[i] for v in pts) for i in range(3)],[max(v[i] for v in pts) for i in range(3)])
 bm.free();ev.to_mesh_clear()
roof_end=max(b[1][1] for n,b in bounds.items() if n.startswith('Nave_Roof'))
tower_start=bounds['Tower_Shaft_Centred'][0][1]
porch_top=max(b[1][2] for n,b in bounds.items() if n.startswith('Porch_Roof'))
window_bottom=min(b[0][2] for n,b in bounds.items() if n.startswith('Front_Gothic_Window'))
shaft_top=bounds['Tower_Shaft_Centred'][1][2];belfry_bottom=bounds['Belfry_Continuous_Masonry'][0][2]
assert tower_start>roof_end,(tower_start,roof_end)
assert window_bottom>porch_top,(window_bottom,porch_top)
assert shaft_top<belfry_bottom,(shaft_top,belfry_bottom)
assert abs(sum(bounds['Tower_Shaft_Centred'][i][0] for i in [0,1]))<1e-5
report={'saved_blend_readback':True,'mesh_objects':len(bounds),'installed_triangles':tris,'issues':issues,'roof_rear_y':roof_end,'tower_shaft_front_y':tower_start,'roof_to_shaft_gap_m':tower_start-roof_end,'porch_top_z':porch_top,'window_surround_bottom_z':window_bottom,'porch_window_clearance_m':window_bottom-porch_top,'shaft_top_z':shaft_top,'belfry_bottom_z':belfry_bottom,'tower_on_centreline':True,'source_stone':'SM_StoneWall_A / Wall_Stone','engine_ready':False}
(P/'readback_qa.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
assert not issues,issues
