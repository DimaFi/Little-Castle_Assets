"""Read-only comparison against deterministic v004 baseline. Never saves user source."""
import bpy, sys, json, hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent
OLD=HERE.parent/'v004'
sys.path.insert(0,str(OLD))
import build_fortifications as f
from optimize_geometry import optimize_assets

def describe(ob):
    d={'type':ob.type,'collections':[c.name for c in ob.users_collection],
       'parent':ob.parent.name if ob.parent else None,
       'location':list(ob.location),'rotation':list(ob.rotation_euler),'scale':list(ob.scale),
       'world_matrix':[list(row) for row in ob.matrix_world]}
    if ob.type=='MESH':
        xyz=[list(v.co) for v in ob.data.vertices]
        d.update(mesh=ob.data.name,vertices=len(xyz),faces=len(ob.data.polygons),
          coordinate_sha=hashlib.sha256(json.dumps(xyz).encode()).hexdigest(),
          bounds=[[min(v[i] for v in xyz) for i in range(3)],[max(v[i] for v in xyz) for i in range(3)]],
          materials=[m.name if m else None for m in ob.data.materials])
    return d

bpy.ops.wm.read_factory_settings(use_empty=True)
f.build();optimize_assets(f.ASSETS)
bpy.context.view_layer.update()
baseline={ob.name:describe(ob) for ob in bpy.data.objects}
original_points={ob.name:[v.co.copy() for v in ob.data.vertices] for ob in bpy.data.objects if ob.type=='MESH'}
bpy.ops.wm.open_mainfile(filepath=str(OLD/'Wall_Fortifications.blend'))
current={ob.name:describe(ob) for ob in bpy.data.objects}
changes={}
for name,d in current.items():
    if name in baseline:
        changed={k:{'before':baseline[name].get(k),'after':v} for k,v in d.items() if v!=baseline[name].get(k)}
        if changed:changes[name]=changed
    else:changes[name]={'gallery_or_added':d}
report={'source':str(OLD/'Wall_Fortifications.blend'),
        'source_sha256':hashlib.sha256((OLD/'Wall_Fortifications.blend').read_bytes()).hexdigest(),
        'changes':changes,'removed':[n for n in baseline if n not in current]}
report['edited_mesh_vertices']={}
for name,d in changes.items():
    if 'coordinate_sha' not in d:continue
    old=original_points[name];now=bpy.data.objects[name].data.vertices
    report['edited_mesh_vertices'][name]=[{'index':v.index,'before':list(old[v.index]) if v.index<len(old) else None,'after':list(v.co)}
        for v in now if v.index>=len(old) or (v.co-old[v.index]).length>1e-6]
(HERE/'QA').mkdir(parents=True,exist_ok=True)
(HERE/'QA/user_changes.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
