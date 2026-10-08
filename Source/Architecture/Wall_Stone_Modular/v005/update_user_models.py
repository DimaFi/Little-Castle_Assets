"""Promote saved manual edits to all exports; never regenerate approved LOD0 geometry."""
import bpy, bmesh, math, json, hashlib, sys
from pathlib import Path
from mathutils import Vector
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import fortification_helpers as f
from check_gate_sweep import sweep
w=f.w
SCALE=1.5466760396957397
HINGE_X=.60
OVERLAP=.08*SCALE
SOURCE=HERE/'Input/UserEdits_2026-10-06.blend'

def load_assets():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    if bpy.context.object and bpy.context.object.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
    previous=json.loads((HERE.parent/'v004/QA/geometry_report.json').read_text())
    for name,entry in previous['assets'].items():
        root=bpy.data.objects[name];coll=bpy.data.collections[name]
        levels=[[bpy.data.objects[p['name']] for p in level['parts']] for level in entry['lods']]
        flat=[o for level in levels for o in level]
        extras=[o for o in coll.objects if o!=root and o not in flat]
        f.ASSETS[name]={'root':root,'collection':coll,'levels':levels,'lods':flat,'extras':extras}
    w.STUDIO=bpy.data.collections['90_PREVIEW_ONLY_DO_NOT_EXPORT']
    # The gallery copies share meshes with production objects. Apply their scale
    # exactly once to each production mesh, then use identity-root fresh instances.
    gallery=bpy.data.objects['SM_Wall_Stone_2m_A_LOD0.001']
    assert max(abs(v-SCALE) for v in gallery.scale)<1e-6
    for name in w.NAMES[:4]:
        a=f.ASSETS[name]
        for ob in a['lods']+[o for o in a['extras'] if o.type=='MESH']:
            for v in ob.data.vertices:v.co*=SCALE
            ob.data.update()
        for ob in a['extras']:
            if ob.type=='EMPTY':
                ob.location*=SCALE
                if ob['export_name'].startswith('BannerAnchor'):ob.scale*=SCALE
    for ob in f.ASSETS[f.GATE]['extras']:
        if ob.type=='EMPTY' and ob.get('export_name','').startswith('GateHinge_'):ob.location.x=HINGE_X
    # LOD0 retains every saved roof edit. Match lowered ridge/finial in distant LODs.
    ridge_delta=-.014782428741455078
    finial_delta=-.0022242069244384766
    for lod in [1,2]:
        mesh=bpy.data.objects[f'SM_ArcherTower_A_Roof_LOD{lod}'].data
        for v in mesh.vertices:
            x,y,z=v.co
            ridge_z=2.776+.73*(1-(abs(x)+abs(y))/(2*1.19))
            if lod==1 and abs(abs(x)-abs(y)-.035)<2e-5 and abs(z-ridge_z)<2e-5:
                v.co.z+=ridge_delta
            elif (abs(z-3.46)<2e-5 and max(abs(x),abs(y))<.066) or abs(z-3.60)<2e-5:
                v.co.z+=finial_delta
        mesh.update()
    cleanup=[]
    for a in f.ASSETS.values():
        for ob in a['lods']:
            bm=bmesh.new();bm.from_mesh(ob.data)
            bmesh.ops.triangulate(bm,faces=list(bm.faces))
            bad=[p for p in bm.faces if p.calc_area()<1e-10]
            count=len(bad)
            if bad:bmesh.ops.delete(bm,geom=bad,context='FACES')
            bm.to_mesh(ob.data);bm.free();ob.data.update()
            uv=ob.data.uv_layers.active;fixed=0
            for p in ob.data.polygons:
                q,r,s=[uv.data[i].uv for i in p.loop_indices]
                if abs((r.x-q.x)*(s.y-q.y)-(r.y-q.y)*(s.x-q.x))>=2e-12:continue
                axes=sorted(range(3),key=lambda i:abs(p.normal[i]))[:2]
                for li in p.loop_indices:
                    co=ob.data.vertices[ob.data.loops[li].vertex_index].co
                    uv.data[li].uv=(.3+co[axes[0]]*.8,.3+co[axes[1]]*.8)
                fixed+=1
            if count or fixed:cleanup.append({'mesh':ob.name,'zero_area_faces_removed':count,'zero_area_uv_faces_repaired':fixed})
    (HERE/'QA/manual_mesh_cleanup.json').write_text(json.dumps(cleanup,indent=2),encoding='utf-8')
    bpy.context.view_layer.update()

def draw_gate(angle=0,lod=0):
    f.instance(f.GATE,lod=lod)
    f.instance(f.LEFT,(HINGE_X,0,-1.04),angle,lod)
    f.instance(f.RIGHT,(HINGE_X,0,1.04),-angle,lod)

def preview():
    for a in f.ASSETS.values():a['collection'].hide_render=True
    blue=w.material('QA_FabricBlue',(.025,.105,.22),.96)
    gold=w.material('QA_TrimGold',(.60,.34,.07),.8)
    half=SCALE;step=2*SCALE-OVERLAP
    w.reset_studio();f.instance(f.TOWER)
    f.banner((.925,1.83,0),90,1.5,blue,gold);f.emblem((.925,1.83,0),90,1.5,gold)
    for sign in [-1,1]:
        for i in range(2):f.instance(w.NAMES[0],(0,0,sign*(.90+half-OVERLAP+i*step)))
    w.render('Updated_Tower_and_Walls.png',(9,5,-9),(0,1.5,0),12,(1600,1100))
    for angle in [0,45,90]:
        w.reset_studio();draw_gate(angle)
        for sign in [-1,1]:f.instance(w.NAMES[0],(0,0,sign*(1.99+half-OVERLAP)))
        w.render(f'Gate_Interior_{angle:02}.png',(7,3.7,-4),(0,1.4,0),9,(1400,1000))
    w.reset_studio();draw_gate(0)
    w.render('Gate_Exterior_Closed.png',(-7,3.7,4),(0,1.4,0),6,(1200,1000))
    w.reset_studio()
    for lod in range(3):f.instance(f.TOWER,(0,0,(lod-1)*3),lod=lod)
    w.render('Tower_LODs.png',(9,6,-7),(0,1.4,0),12,(1500,950))

if __name__=='__main__':
    for folder in ['Meshes','Preview','QA']:(HERE/folder).mkdir(exist_ok=True)
    source_hash=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    load_assets()
    f.CONTRACT={'version':'v005','unity_tested':False,'coordinates':'metres, Y-up, wall axis Z',
                'assets':{},'manual_source_sha256':source_hash,'wall_scale':SCALE,
                'segment_length':2*SCALE,'short_segment_length':SCALE,
                'recommended_overlap_m':OVERLAP,'gate_interior_axis':'+X','hinge_x':HINGE_X}
    f.export_report()
    connections=json.loads((HERE/'Connections.json').read_text())
    connections.update(version='v005',recommended_overlap_m=OVERLAP,
                       segment_length=2*SCALE,short_segment_length=SCALE,
                       gate={'interior_axis':'+X','exterior_axis':'-X','hinge_x':HINGE_X,
                             'left_open_y_degrees':90,'right_open_y_degrees':-90})
    (HERE/'Connections.json').write_text(json.dumps(connections,indent=2),encoding='utf-8')
    sweeps=[sweep(HINGE_X,lod,.5) for lod in range(3)]
    assert not any(r['collisions'] for r in sweeps),sweeps
    (HERE/'QA/gate_sweep.json').write_text(json.dumps({'status':'PASS','tests':sweeps,
       'scope':'triangle intersection with frame, 0..90 degrees every 0.5 degrees, both leaves all LODs'},indent=2),encoding='utf-8')
    sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=24;sc.cycles.use_denoising=True
    sc.render.image_settings.file_format='PNG';sc.render.resolution_percentage=100;sc.view_settings.view_transform='AgX'
    for im in bpy.data.images:
        if im.source=='FILE':
            local=HERE/'Textures'/Path(im.filepath).name
            if local.exists():im.filepath=str(local)
    preview()
    w.reset_studio();f.instance(f.TOWER,(0,0,-3));draw_gate(0)
    f.instance(w.NAMES[0],(0,0,1.99+SCALE-OVERLAP))
    w.camera((10,6,-7),(0,1.5,0),11)
    for a in f.ASSETS.values():
        for ob in [a['root']]+a['lods']+a['extras']:ob.hide_set(True)
    for im in bpy.data.images:
        if im.source=='FILE' and not im.packed_file:im.pack()
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'Wall_Fortifications.blend'))
    f.CONTRACT['source_sha256']=hashlib.sha256((HERE/'Wall_Fortifications.blend').read_bytes()).hexdigest()
    (HERE/'QA/geometry_report.json').write_text(json.dumps(f.CONTRACT,indent=2),encoding='utf-8')
    assert source_hash==hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    print('MANUAL_MODELS_UPDATED',flush=True)
