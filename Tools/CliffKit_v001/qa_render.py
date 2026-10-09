"""Real Blender mesh/FBX roundtrip QA and repeatable visual evidence."""
import bpy,bmesh,json,math,sys
from pathlib import Path
from mathutils import Vector
from mathutils.kdtree import KDTree
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'Source/Environment/CliffKit/v001';QA=OUT/'QA'

def audit(ob):
    mesh=ob.data;bm=bmesh.new();bm.from_mesh(mesh)
    boundary=sum(not e.is_manifold for e in bm.edges);volume=bm.calc_volume(signed=True);bm.free()
    degenerate=sum(p.area<1e-9 for p in mesh.polygons)
    uv=mesh.uv_layers.active
    zero_uv=0
    for p in mesh.polygons:
        pts=[uv.data[q].uv for q in p.loop_indices]
        area=abs(sum(pts[i].x*pts[(i+1)%len(pts)].y-pts[(i+1)%len(pts)].x*pts[i].y for i in range(len(pts))))
        zero_uv+=area<1e-10
    assert boundary==0,(ob.name,'nonmanifold',boundary)
    assert degenerate==0,(ob.name,'degenerate',degenerate)
    assert volume>0,(ob.name,'inside out',volume)
    assert zero_uv==0,(ob.name,'UV collapse',zero_uv)
    return dict(name=ob.name,vertices=len(mesh.vertices),triangles=sum(len(p.vertices)-2 for p in mesh.polygons),nonmanifold_edges=boundary,zero_area_faces=degenerate,zero_area_uv=zero_uv,volume_m3=volume)

def lighting():
    scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=12
    scene.cycles.use_denoising=True
    scene.render.resolution_x=560;scene.render.resolution_y=420;scene.render.resolution_percentage=100
    scene.view_settings.view_transform='AgX'
    scene.world.color=(.32,.32,.32)
    nodes=scene.world.node_tree.nodes if scene.world.use_nodes else None
    scene.world.use_nodes=True;scene.world.node_tree.nodes.get('Background').inputs[0].default_value=(.48,.58,.7,1)
    scene.world.node_tree.nodes.get('Background').inputs[1].default_value=.55
    bpy.ops.object.light_add(type='AREA',location=(-12,10,26));sun=bpy.context.object
    sun.data.energy=4500;sun.data.shape='DISK';sun.data.size=12
    sun.rotation_euler=(Vector((0,0,2))-sun.location).to_track_quat('-Z','Y').to_euler()
    bpy.ops.object.light_add(type='SUN',location=(0,0,20));sun=bpy.context.object
    sun.data.energy=2;sun.data.angle=.22;sun.rotation_euler=(.4,-.55,-.5)
    bpy.ops.object.camera_add();scene.camera=bpy.context.object;scene.camera.data.type='ORTHO'
    # Neutral ground plane gives scale and shadows, never shipped as an asset.
    bpy.ops.mesh.primitive_plane_add(size=400,location=(0,0,-.46));ground=bpy.context.object
    mat=bpy.data.materials.new('QA_Ground');mat.diffuse_color=(.29,.34,.18,1);ground.data.materials.append(mat)
    return ground

def render(ob,cfg,angle,path):
    ob.hide_render=False;ob.hide_set(False);ob.location=(0,0,0)
    w,h,d=cfg['width'],cfg['height'],cfg['depth']
    target=Vector((0,-d/2,h*.45))
    cam=bpy.context.scene.camera
    distance=max(w,d,h)*1.45
    cam.location=target+Vector((math.sin(angle)*distance,math.cos(angle)*distance,distance*.75))
    cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.ortho_scale=max(w,d*.85,h)*1.5
    bpy.context.scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)
    ob.hide_render=True

def main():
    QA.mkdir(exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(OUT/'CliffKit.blend'))
    catalog=json.loads((OUT/'ASSET_CATALOG.json').read_text())
    records=[]
    for ob in bpy.data.objects:
        if ob.type=='MESH':records.append(audit(ob));ob.hide_render=True
    # Compare source local positions to the actual reimported FBX geometry in Blender world space.
    roundtrip=[]
    for cfg in catalog['assets']:
        for lod,path in enumerate(cfg['lod_fbx']):
            original=bpy.data.objects[cfg['id']+'_LOD'+str(lod)]
            expected=KDTree(len(original.data.vertices))
            for i,v in enumerate(original.data.vertices):expected.insert(v.co,i)
            expected.balance()
            before=set(bpy.data.objects)
            bpy.ops.import_scene.fbx(filepath=str(OUT/path))
            imported=[o for o in bpy.data.objects if o not in before]
            mesh=next(o for o in imported if o.type=='MESH')
            error=max(expected.find(mesh.matrix_world@v.co)[2] for v in mesh.data.vertices)
            assert len(mesh.data.vertices)==len(original.data.vertices) and error<.0001,(path,'FBX basis or scale mismatch',error)
            assert len(mesh.data.polygons)==len(original.data.polygons)
            roundtrip.append(dict(file=path,position_max_error_m=error,**audit(mesh)))
            for ob in imported:bpy.data.objects.remove(ob,do_unlink=True)
    (QA/'geometry.json').write_text(json.dumps(dict(blender=bpy.app.version_string,source=records,fbx_roundtrip=roundtrip,status='PASS'),indent=2)+'\n')
    lighting()
    subset=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    for cfg in catalog['assets']:
        if subset and cfg['id'] not in subset:continue
        for lod in range(3):
            ob=bpy.data.objects[cfg['id']+'_LOD'+str(lod)]
            render(ob,cfg,.42,QA/f'{cfg["id"]}_LOD{lod}.png')
        for label,a in [('front',0),('rear',2.9)]:
            render(bpy.data.objects[cfg['id']+'_LOD0'],cfg,a,QA/f'{cfg["id"]}_{label}.png')
    print('CLIFFKIT_QA_PASS 42 manifold meshes + 42 FBX roundtrips; visual review separate')

if __name__=='__main__':main()
