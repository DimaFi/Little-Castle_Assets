import bpy,bmesh,json,math
from pathlib import Path
P=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(P/'Church_A.blend'))
deps=bpy.context.evaluated_depsgraph_get();issues=[];tris=0;leaf_tris=0;materials=set();meshes=0
for o in bpy.context.scene.objects:
 if o.type!='MESH' or any(c.name=='90_STUDIO' for c in o.users_collection):continue
 meshes+=1;isleaf=bool(o.get('intentional_open_surface'))
 ev=o.evaluated_get(deps);me=ev.to_mesh();me.calc_loop_triangles();tris+=len(me.loop_triangles)
 if isleaf:leaf_tris+=len(me.loop_triangles)
 if any(t.area<1e-10 for t in me.loop_triangles):issues.append(o.name+': degenerate')
 bm=bmesh.new();bm.from_mesh(me)
 if not isleaf and any(not e.is_manifold for e in bm.edges):issues.append(o.name+': nonmanifold')
 bm.free();ev.to_mesh_clear()
 for mat in o.data.materials:
  if not mat:issues.append(o.name+': missing material');continue
  materials.add(mat.name)
  if mat.name.startswith('Clay_Grey'):issues.append(o.name+': unpainted')
 if not o.data.uv_layers.get('UV0') and not o.name.endswith('_Stems'):issues.append(o.name+': missing UV0')
images={}
for m in bpy.data.materials:
 if m.name not in materials or not m.use_nodes:continue
 for n in m.node_tree.nodes:
  if n.type=='TEX_IMAGE':
   if not n.image:issues.append(m.name+': missing image')
   else:
    images[n.image.name]=bool(n.image.packed_file)
    if not n.image.packed_file:issues.append(n.image.name+': not packed')
# Continuous stone cheek backing reaches ground on both sides and meets the house.
backing=[o for o in bpy.data.objects if o.name.startswith('StairSide_InnerBacking')]
assert len(backing)==2
for o in backing:
 pts=[o.matrix_world@v.co for v in o.data.vertices]
 assert min(v.z for v in pts)<=.001 and max(v.y for v in pts)>=-3.7
assert tris<52000,tris
result={'saved_file_checked':True,'mesh_objects':meshes,'triangles':tris,'foliage_leaf_triangles':leaf_tris,'foliage_open_edges_intentional':True,'packed_images':images,'used_materials':sorted(materials),'stair_cheeks_closed_to_ground':True,'issues':issues}
(P/'readback_qa.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2));assert not issues,issues
