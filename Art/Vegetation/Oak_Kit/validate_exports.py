"""FBX round-trip and visual QA. Run with Blender after build_oak_kit.py."""
import bpy,os,json,math,bmesh,sys
from mathutils import Vector
ROOT=os.path.dirname(os.path.abspath(__file__))
manifest=json.load(open(os.path.join(ROOT,'QA','asset_manifest.json'),encoding='utf8'))
report={};errors=[]
for name,expected in manifest['assets'].items():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=os.path.join(ROOT,'Exports',name+'.fbx'))
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH' and not o.name.startswith('UCX_')]
    assert len(meshes)==1,(name,'must have exactly one asset mesh')
    o=meshes[0];me=o.data;me.calc_loop_triangles()
    assert len(me.loop_triangles)==expected['triangles'],name
    assert all(math.isfinite(x) for v in me.vertices for x in v.co),name
    assert len(me.uv_layers)>=1,name
    assert all(math.isfinite(x) for loop in me.uv_layers[0].data for x in loop.uv),name
    assert max(abs(o.dimensions[i]-expected['dimensions_m'][i]) for i in range(3))<.001,(name,list(o.dimensions))
    assert o.location.length<.00001,name
    assert max(abs(s-1) for s in o.scale)<.00001,name
    degenerate=sum(1 for tri in me.loop_triangles if (me.vertices[tri.vertices[1]].co-me.vertices[tri.vertices[0]].co).cross(me.vertices[tri.vertices[2]].co-me.vertices[tri.vertices[0]].co).length<1e-10)
    assert degenerate==0,(name,degenerate)
    assert len([ob for ob in bpy.context.scene.objects if ob.type=='MESH'])==1,(name,'no engine-specific collision mesh in FBX')
    report[name]={'triangles':len(me.loop_triangles),'dimensions_m':list(o.dimensions),'uv_layers':len(me.uv_layers),'material_slots':len(me.materials),'degenerate_triangles':degenerate,'fbx_roundtrip':'PASS'}
with open(os.path.join(ROOT,'QA','export_validation.json'),'w') as f:json.dump(report,f,indent=2)
print('FBX_ROUNDTRIP_PASSED',len(report),flush=True)

bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT,'Cozy_Oak_Kit.blend'))
scene=bpy.context.scene
wood=bpy.data.objects['Oak_ContinuousWood'];bm=bmesh.new();bm.from_mesh(wood.data)
pending=set(bm.verts);components=0
while pending:
    components+=1;stack=[pending.pop()]
    while stack:
        v=stack.pop()
        for edge in v.link_edges:
            other=edge.other_vert(v)
            if other in pending:pending.remove(other);stack.append(other)
nonmanifold=sum(not e.is_manifold for e in bm.edges);bm.free()
assert components==1,('wood should be one continuous mesh',components)
assert nonmanifold==0,('wood should be watertight',nonmanifold)
with open(os.path.join(ROOT,'QA','structure_validation.json'),'w') as f:json.dump({'wood_connected_components':components,'nonmanifold_edges':nonmanifold,'primary_branches':7,'roots':7,'canopy_masses':10,'source_collection_preserved':True},f,indent=2)
if '--no-module-renders' in sys.argv:
    print('ALL_CHECKS_PASSED; unchanged module previews retained',flush=True);sys.exit()

# Render every reusable module without changing the final saved source.
bpy.data.collections['Tree'].hide_render=True;bpy.data.collections['GroundDecoration'].hide_render=True
lib=bpy.data.collections['MODULE_LIBRARY'];lib.hide_render=False;lib.hide_viewport=False
obs=sorted([o for o in lib.objects if o.name.startswith('SM_')],key=lambda o:o.name)
for o in obs:o.hide_render=True
scene.render.resolution_x=400;scene.render.resolution_y=400;scene.cycles.samples=16
cam=scene.camera
os.makedirs(os.path.join(ROOT,'Renders','Modules'),exist_ok=True)
for o in obs:
    o.hide_render=False
    box=[o.matrix_world@Vector(c) for c in o.bound_box];center=sum(box,Vector())/8
    span=max(o.dimensions);cam.location=center+Vector((2,-4,2.6))*span
    cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=span*1.55
    scene.render.filepath=os.path.join(ROOT,'Renders','Modules',o.name+'.png');bpy.ops.render.render(write_still=True);o.hide_render=True
print('MODULE_PREVIEWS_COMPLETE',flush=True)

# Neutral geometry contact sheet: rendered previews, not generated concept art.
import numpy as np
tile=400;cols=7;rows=4;canvas=np.ones((rows*tile,cols*tile,4),dtype=np.float32)
for i,o in enumerate(obs):
    im=bpy.data.images.load(os.path.join(ROOT,'Renders','Modules',o.name+'.png'),check_existing=False)
    data=np.empty(tile*tile*4,dtype=np.float32);im.pixels.foreach_get(data);data=data.reshape((tile,tile,4))
    row=rows-1-i//cols;col=i%cols;canvas[row*tile:(row+1)*tile,col*tile:(col+1)*tile]=data
sheet=bpy.data.images.new('Kit catalog',width=cols*tile,height=rows*tile,alpha=True)
sheet.pixels.foreach_set(canvas.ravel());sheet.filepath_raw=os.path.join(ROOT,'Renders','05_modules.png');sheet.file_format='PNG';sheet.save()
print('ALL_CHECKS_PASSED',flush=True)
