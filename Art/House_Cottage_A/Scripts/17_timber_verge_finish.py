"""v011: finish v010 timber pass by trimming only main tile edges at timber verges."""
import sys, json, runpy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from kit_geometry import *
helper=runpy.run_path(str(Path(__file__).with_name('16_timber_materials.py')),run_name='timber_helpers')
ROOT=Path(__file__).resolve().parents[1];REND=ROOT/'Renders/Checkpoint_07/v011'
LIMIT=3.475  # Verge inner edge 3.470: 5 mm of concealed overlap.

def trim():
    changes=[]
    cutter=box('TEMP_Verge_Trim_Volume',(0,0,4),(2*LIMIT,20,20),
               bpy.data.collections['05_ROOF'],bpy.data.materials['M_Blockout_Grey'],0)
    cutter.hide_render=True
    for o in list(bpy.data.collections['ROOF_TILES_MAIN'].objects):
        xs=[(o.matrix_world@v.co).x for v in o.data.vertices]
        if min(xs)>=-LIMIT and max(xs)<=LIMIT:continue
        o.data=o.data.copy();active(o)
        bm=bmesh.new();bm.from_mesh(o.data);open_surface=any(e.is_boundary for e in bm.edges);bm.free()
        # Legacy baked prototypes lost their thickness. Restore the intended
        # inward clay thickness on edited border pieces before making a closed cut.
        if open_surface:
            shell=o.modifiers.new('Restore clay thickness on border tile','SOLIDIFY')
            shell.thickness=.035;shell.offset=-1;shell.use_rim=True
            bpy.ops.object.modifier_apply(modifier=shell.name)
        mod=o.modifiers.new('Closed trim inside timber verges','BOOLEAN')
        mod.operation='INTERSECT';mod.solver='EXACT';mod.object=cutter
        bpy.ops.object.modifier_apply(modifier=mod.name)
        bm=bmesh.new();bm.from_mesh(o.data)
        bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7)
        bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=1e-7)
        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
        assert bm.faces,('Unexpected empty edge tile',o.name)
        assert not any(e.is_boundary for e in bm.edges),('Open cut',o.name)
        bm.to_mesh(o.data);bm.free();o.data.update()
        o['verge_trim']='v011: closed trim at world X +/- 3.475 m; timber overlap 5 mm'
        changes.append(o.name)
    bpy.data.objects.remove(cutter,do_unlink=True)
    bpy.context.view_layer.update()
    stats=inspect_geometry([bpy.data.objects[n] for n in changes]);assert not stats['issues'],stats
    for name in changes:
        o=bpy.data.objects[name]
        assert all(abs((o.matrix_world@v.co).x)<=LIMIT+1e-5 for v in o.data.vertices),name
    return changes,stats

def paths(mode,version):
    return ROOT/'Source'/('Materials' if mode=='house' else 'Assembly')/version/('House_Cottage_A.blend' if mode=='house' else 'Cottage_Courtyard.blend')

def build(mode):
    target=paths(mode,'v011');assert not target.exists(),target
    bpy.ops.wm.open_mainfile(filepath=str(paths(mode,'v010')));sc=bpy.context.scene;bpy.context.view_layer.update()
    before=helper['digest'](list(bpy.data.objects));changes,stats=trim();after=helper['digest'](list(bpy.data.objects))
    assert {n:h for n,h in before.items() if n not in changes}=={n:h for n,h in after.items() if n not in changes}
    target.parent.mkdir(parents=True,exist_ok=True);bpy.ops.wm.save_as_mainfile(filepath=str(target))
    report={'file':str(target.relative_to(ROOT)),'trimmed_tiles':changes,'trim_geometry':stats,'all_other_geometry_and_pivots_unchanged':True}
    (ROOT/'QA'/('timber_v011_'+mode+'.json')).write_text(json.dumps(report,indent=2),encoding='utf-8')
    if mode=='house':
        render(sc,sc.camera,REND/'House_Hero.png',1000)
        st=bpy.data.collections['90_STUDIO - not exported']
        cam=camera('QA_Timber_Detail',(-8,-7,6.3),(-1.3,-.8,3.25),5.8,st)
        render(sc,cam,REND/'Timber_Detail.png',900)
        cam=camera('QA_Timber_Rear',(8,9,7),(0,0,2.9),9.5,st)
        render(sc,cam,REND/'House_Rear.png',900)
    else:render(sc,sc.camera,REND/'Courtyard_Hero.png',1100)
    print('VERGE_FINISH_COMPLETE',mode,len(changes),flush=True)

def validate():
    report=[]
    for mode in ['house','assembly']:
        data=json.loads((ROOT/'QA'/('timber_v011_'+mode+'.json')).read_text(encoding='utf-8'));changed=data['trimmed_tiles']
        bpy.ops.wm.open_mainfile(filepath=str(paths(mode,'v010')));bpy.context.view_layer.update()
        before=helper['digest'](list(bpy.data.objects))
        bpy.ops.wm.open_mainfile(filepath=str(paths(mode,'v011')));bpy.context.view_layer.update()
        after=helper['digest'](list(bpy.data.objects))
        assert {n:h for n,h in before.items() if n not in changed}=={n:h for n,h in after.items() if n not in changed}
        trimstats=inspect_geometry([bpy.data.objects[n] for n in changed]);assert not trimstats['issues'],trimstats
        for name in changed:
            o=bpy.data.objects[name];bm=bmesh.new();bm.from_mesh(o.data)
            assert all(e.is_manifold for e in bm.edges),name;bm.free()
            assert all(abs((o.matrix_world@v.co).x)<=LIMIT+1e-5 for v in o.data.vertices),name
        woodstats=helper['verify'](helper['targets']())
        report.append({'name':mode,'trimmed_tiles':len(changed),'closed_cuts':True,'other_geometry_unchanged':True,'timber':woodstats})
    (ROOT/'QA/timber_v011_readback.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('VERGE_READBACK_COMPLETE',len(report),flush=True)

REND.mkdir(parents=True,exist_ok=True)
mode=sys.argv[sys.argv.index('--')+1]
if mode=='validate':validate()
else:build(mode)
