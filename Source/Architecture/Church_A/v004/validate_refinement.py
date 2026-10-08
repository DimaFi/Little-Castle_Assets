import bpy,bmesh,json,math
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(P/'Church_A.blend'))
deps=bpy.context.evaluated_depsgraph_get();issues=[];tris=0;open_tiles=0;images={};bounds={}
for o in bpy.context.scene.objects:
 if o.type!='MESH' or any(c.name=='90_STUDIO' for c in o.users_collection):continue
 ev=o.evaluated_get(deps);me=ev.to_mesh();me.calc_loop_triangles();tris+=len(me.loop_triangles)
 bm=bmesh.new();bm.from_mesh(me)
 intentional=bool(o.get('intentional_open_surface') or o.get('covered_face_culling'))
 if o.get('covered_face_culling'):open_tiles+=1
 if not intentional and any(not e.is_manifold for e in bm.edges):issues.append(o.name+': unexpected open edge')
 if any(t.area<1e-10 for t in me.loop_triangles):issues.append(o.name+': degenerate')
 if any(not all(math.isfinite(c) for c in v.co) for v in me.vertices):issues.append(o.name+': nonfinite')
 pts=[o.matrix_world@v.co for v in me.vertices]
 bounds[o.name]=([min(v[i] for v in pts) for i in range(3)],[max(v[i] for v in pts) for i in range(3)])
 bm.free();ev.to_mesh_clear()
 for m in o.data.materials:
  if not m:issues.append(o.name+': missing material');continue
  for n in m.node_tree.nodes if m.use_nodes else []:
   if n.type=='TEX_IMAGE':
    if not n.image or not n.image.packed_file:issues.append(m.name+': unpacked/missing texture')
    else:images[n.image.name]=True
foot_back=bounds['Front_Cross_Foot'][1][1];ridge_front=bounds['Nave_Roof_Ridge'][0][1]
assert ridge_front-foot_back>.015,(ridge_front,foot_back)
timber=[o for o in bpy.context.scene.objects if o.get('uv_metres_to_repeat')]
assert len(timber)==111 and all(abs(o['uv_metres_to_repeat']-.64)<1e-7 for o in timber)
for sign in [-1,1]:
 stones=[o for o in bpy.context.scene.objects if o.name.startswith('Stair_Bonded_'+str(sign))]
 assert len(stones)==8,len(stones)
 assert min(bounds[o.name][0][2] for o in stones)<.004
assert tris<50746
report={'saved_file_readback':True,'triangles':tris,'reduction_from_v003':50746-tris,'reduction_percent':round((50746-tris)/50746*100,2),'metric_timber_uv_objects':len(timber),'interior_tiles_with_deliberate_culling':open_tiles,'cross_to_ridge_gap_m':ridge_front-foot_back,'packed_used_images':len(images),'issues':issues}
(P/'readback_qa.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2));assert not issues,issues
