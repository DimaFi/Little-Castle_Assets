"""v018: expose corner timber and reduce excessive dormer tile clearance.
Blender -- [preview|house|assembly|validate|module]. No previous files overwritten.
"""
import sys,json,math,runpy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from kit_geometry import *
from mathutils import Matrix
ROOT=Path(__file__).resolve().parents[1]
REND=ROOT/'Renders/Checkpoint_13/v018'
ROOF=runpy.run_path(str(Path(__file__).with_name('22_roof_materials.py')),run_name='roof_helpers')
TIMBER=runpy.run_path(str(Path(__file__).with_name('16_timber_materials.py')),run_name='timber_helpers')
RIDGE=runpy.run_path(str(Path(__file__).with_name('25_seat_ridge_plaster.py')),run_name='ridge_helpers')

def source(mode,version):
    return ROOT/'Source'/('Assembly' if mode=='assembly' else 'Roof')/version/('Cottage_Courtyard.blend' if mode=='assembly' else 'House_Cottage_A.blend')

def rz(x,y):
    t=abs(y)/2.94
    return 5.64-.22*(1-(x/3.57)**2)-3.05*t+.62*t*t+(.035 if y>0 else 0)*t+.025*(x/3.57)*t

def make_tile(name,width,length,col,mat):
    vv=[];ff=[]
    for j in range(4):
        t=j/3
        for i in range(5):
            u=i/4;vv.append(((u-.5)*(width-(.018 if j==0 else 0)),length*t,.016*math.sin(math.pi*u)+.020*(1-t)))
    for j in range(3):
        for i in range(4):
            k=j*5+i;ff.append((k,k+1,k+6,k+5))
    o=mesh(name,vv,ff,col,mat);active(o)
    m=o.modifiers.new('Clay thickness','SOLIDIFY');m.thickness=.035;m.offset=-1;m.use_rim=True
    bpy.ops.object.modifier_apply(modifier=m.name)
    return o

def fix():
    changed=[];created=[];deleted=[]
    for o in bpy.data.collections['04_TIMBER'].objects:
        if o.name.startswith('SM_Beam_Corner_A'):
            o.location.x+=.09 if o.location.x>0 else -.09
            o['junction_fix']='v018: post shifted outward 90 mm to expose side face clear of plaster'
            changed.append(o.name)
    bpy.context.view_layer.update()
    hood=bpy.data.objects['SM_Dormer_Hood_A']
    joint=[(v.co.x,v.co.y) for v in list(hood.data.vertices)[-33:]]
    # Hidden overlap: clay meets hood above the structural roof intersection.
    poly=[(.52-.64,-2.17),(.52+.64,-2.17)]+[(x,y-.09) for x,y in reversed(joint)]
    n=len(poly);vv=[(x,y,z) for z in [2.7,7] for x,y in poly]
    ff=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    col=bpy.data.collections['ROOF_TILES_MAIN'];mat=bpy.data.materials['M_Cottage_Terracotta_A']
    cutter=mesh('TEMP_Fitted_Dormer_Cut',vv,ff,col,mat);cutter.hide_render=True
    # Rebuild only the small front-roof rectangle touching the old dormer cut.
    # Original row spacing, profile, transforms and deterministic variations retained.
    for row in range(11):
        ay=2.98-row*.28;y=-ay
        dy=(rz(0,y+.001)-rz(0,y-.001))/.002
        length=min(.52,ay*math.sqrt(1+dy*dy)+.065)
        bounds=[-3.61];q=-3.61+(.164 if row%2 else .328)
        while q<3.60:bounds.append(q);q+=.328
        bounds.append(3.61)
        for c,(a,b) in enumerate(zip(bounds,bounds[1:])):
            if b-a<.06 or b<-.30 or a>1.34 or y>max(p[1] for p in joint)+.08 or y+length<-2.46:continue
            name=f'SM_Tile_-1_{row:02}_{c:02}';old=bpy.data.objects.get(name)
            o=make_tile('TEMP_Fitted_Tile',b-a-.008,length,col,mat)
            x=(a+b)/2;dx=(rz(x+.001,y)-rz(x-.001,y))/.002;dy=(rz(x,y+.001)-rz(x,y-.001))/.002
            normal=Vector((-dx,-dy,1)).normalized();up=Vector((0,1,dy)).normalized();across=up.cross(normal).normalized()
            o.rotation_euler=Matrix((across,up,normal)).transposed().to_euler()
            o.location=Vector((x,y,rz(x,y)))+normal*(.038+.003*(.5+.5*math.sin(c*2.1+row)))
            bpy.context.view_layer.update();active(o)
            mod=o.modifiers.new('Tight dormer junction','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter
            bpy.ops.object.modifier_apply(modifier=mod.name)
            if not o.data.polygons:
                bpy.data.objects.remove(o,do_unlink=True)
                if old:bpy.data.objects.remove(old,do_unlink=True);deleted.append(name)
                continue
            if old:bpy.data.objects.remove(old,do_unlink=True);changed.append(name)
            else:created.append(name)
            o.name=name;o['row']=row;o['stage']='v018 fitted dormer boundary; packed clay material and UV0'
            bm=bmesh.new();bm.from_mesh(o.data)
            bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-5)
            bmesh.ops.triangulate(bm,faces=list(bm.faces))
            bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=1e-5)
            bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
            assert all(e.is_manifold for e in bm.edges),(name,'open tile')
            bm.to_mesh(o.data);bm.free();o.data.update()
            ROOF['unwrap'](o.data,'ROOF_TILES_MAIN')
    bpy.data.objects.remove(cutter,do_unlink=True);bpy.context.view_layer.update()
    return {'changed':changed,'created':created,'deleted':deleted}

def verify(records):
    objs=[bpy.data.objects[n] for n in records['changed']+records['created']]
    stats=inspect_geometry(objs);assert not stats['issues'],stats
    count=0
    for o in objs:
        me=o.data;me.calc_loop_triangles();uv=me.uv_layers['UV0'].data
        for t in me.loop_triangles:
            a,b,c=[uv[i].uv for i in t.loops]
            assert abs((b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x))>1e-12,(o.name,'collapsed UV')
            count+=1
    exposures=[]
    for o in bpy.data.collections['04_TIMBER'].objects:
        if not o.name.startswith('SM_Beam_Corner_A'):continue
        points=[o.matrix_world@v.co for v in o.data.vertices]
        exposure=max(abs(p.x) for p in points)-3.1;assert exposure>.065,(o.name,exposure)
        exposures.append({'name':o.name,'side_exposure_m':exposure})
    stats.update(uv_triangles_checked=count,corner_posts=exposures)
    return stats

def compare(before,after,records):
    exempt=set(records['changed']+records['created']+records['deleted'])
    assert {n:v for n,v in before.items() if n not in exempt}=={n:v for n,v in after.items() if n not in exempt}

def views(sc,prefix=''):
    hero=sc.camera;render(sc,hero,REND/(prefix+'House_Hero.png'),950)
    st=bpy.data.collections['90_STUDIO - not exported']
    cam=camera('QA_Dormer_Fit',(-4,-8,7),(.52,-1.55,4.4),3.3,st)
    render(sc,cam,REND/(prefix+'Dormer_Detail.png'),1000)
    cam=camera('QA_Corner_Post',(-8,-7,4),(-2.7,-1.8,1.9),4.2,st)
    render(sc,cam,REND/(prefix+'Timber_Detail.png'),900)

def build(mode):
    kind='house' if mode=='preview' else mode;target=source(kind,'v018')
    if mode!='preview':assert not target.exists(),target
    bpy.ops.wm.open_mainfile(filepath=str(source(kind,'v017')));bpy.context.view_layer.update()
    before=TIMBER['digest'](list(bpy.data.objects));records=fix();stats=verify(records)
    compare(before,TIMBER['digest'](list(bpy.data.objects)),records)
    sc=bpy.context.scene
    if mode=='preview':views(sc,'Preview_');print('JUNCTION_PREVIEW_COMPLETE',json.dumps(records),flush=True);return
    target.parent.mkdir(parents=True,exist_ok=True);bpy.ops.wm.save_as_mainfile(filepath=str(target))
    report={'records':records,'stats':stats,'other_geometry_unchanged':True,'file':str(target.relative_to(ROOT))}
    (ROOT/'QA'/('junctions_v018_'+mode+'.json')).write_text(json.dumps(report,indent=2),encoding='utf-8')
    if mode=='house':views(sc)
    else:render(sc,sc.camera,REND/'Courtyard_Hero.png',1100)
    print('JUNCTION_COMPLETE',mode,flush=True)

def validate():
    reports=[]
    for mode in ['house','assembly']:
        records=json.loads((ROOT/'QA'/('junctions_v018_'+mode+'.json')).read_text(encoding='utf-8'))['records']
        bpy.ops.wm.open_mainfile(filepath=str(source(mode,'v017')));bpy.context.view_layer.update();before=TIMBER['digest'](list(bpy.data.objects))
        bpy.ops.wm.open_mainfile(filepath=str(source(mode,'v018')));bpy.context.view_layer.update()
        compare(before,TIMBER['digest'](list(bpy.data.objects)),records);stats=verify(records)
        caps=RIDGE['closed_caps']();contacts=RIDGE['audit']();gap=max(r['max_gap'] for r in contacts);assert gap<=.004,gap
        images=[im for im in bpy.data.images if im.source=='FILE' and im.users>0]
        assert all(im.packed_file for im in images),[im.name for im in images if not im.packed_file]
        reports.append({'mode':mode,'stats':stats,'other_geometry_unchanged':True,'ridge_max_gap_m':gap,'packed_images':len(images)})
    (ROOT/'QA/junctions_v018_readback.json').write_text(json.dumps(reports,indent=2),encoding='utf-8')
    print('JUNCTION_READBACK_COMPLETE',flush=True)

def module():
    target=ROOT/'Source/Modules/Timber_v002/SM_Cottage_TimberFrame_A.blend'
    assert not target.exists(),target
    bpy.ops.wm.open_mainfile(filepath=str(source('house','v018')))
    objects=TIMBER['targets']();expected=TIMBER['digest'](objects)
    sc=bpy.data.scenes.new('SM_Cottage_TimberFrame_A_v002');bpy.context.window.scene=sc
    sc.unit_settings.system='METRIC';sc.unit_settings.scale_length=1
    sc.render.engine='CYCLES';sc.cycles.samples=24;sc.cycles.use_denoising=True
    sc.view_settings.view_transform='AgX'
    col=collection('SM_Cottage_TimberFrame_A_v002')
    for original in objects:
        o=original.copy();col.objects.link(o);o.matrix_world=original.matrix_world.copy()
        o['source_object_name']=original.name
    st=studio(sc,bpy.data.materials['M_Blockout_Grey'])
    next(o for o in st.objects if o.name.startswith('Studio ground')).location.z=-.125
    sc.camera=camera('CAM_TimberFrame_v002',(-10,-13,9),(0,0,2.8),10,st)
    temporary=ROOT/'QA/Timber_v002_library_build.blend'
    bpy.data.libraries.write(str(temporary),{sc},fake_user=True)
    bpy.ops.wm.open_mainfile(filepath=str(temporary));sc=bpy.data.scenes['SM_Cottage_TimberFrame_A_v002'];bpy.context.window.scene=sc
    target.parent.mkdir(parents=True,exist_ok=True);bpy.ops.wm.save_as_mainfile(filepath=str(target))
    bpy.ops.wm.open_mainfile(filepath=str(target));assert bpy.context.scene.name=='SM_Cottage_TimberFrame_A_v002'
    saved=[o for o in bpy.context.scene.objects if 'source_object_name' in o]
    assert len(saved)==len(expected)
    actual=TIMBER['digest'](saved)
    for o in saved:assert actual[o.name]==expected[o['source_object_name']]
    (ROOT/'QA/timber_v002_readback.json').write_text(json.dumps({'parts':len(saved),'matches_house_v018':True,'native_scene_saved':True},indent=2),encoding='utf-8')
    temporary.unlink()
    print('TIMBER_V002_COMPLETE',flush=True)

if __name__=='__main__':
    REND.mkdir(parents=True,exist_ok=True);mode=sys.argv[sys.argv.index('--')+1]
    if mode=='validate':validate()
    elif mode=='module':module()
    else:build(mode)
