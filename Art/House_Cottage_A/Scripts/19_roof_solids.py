"""v012 roof thickness audit and repair. Background Blender -- [audit|house|assembly|validate]."""
import sys,json,runpy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from kit_geometry import *
ROOT=Path(__file__).resolve().parents[1]
HELPER=runpy.run_path(str(Path(__file__).with_name('16_timber_materials.py')),run_name='helpers')
GROUPS={'ROOF_TILES_MAIN':.035,'ROOF_TILES_DORMER':.030,'ROOF_RIDGE_CAPS':.040}
REND=ROOT/'Renders/Checkpoint_08/v012'

def topology(me):
    bm=bmesh.new();bm.from_mesh(me)
    result={'vertices':len(bm.verts),'faces':len(bm.faces),
        'boundary_edges':sum(e.is_boundary for e in bm.edges),
        'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),
        'wire_edges':sum(e.is_wire for e in bm.edges),
        'volume':abs(bm.calc_volume(signed=True))}
    bm.free();return result

def audit():
    groups={}
    for name in GROUPS:
        objects=list(bpy.data.collections[name].objects)
        meshes={o.data for o in objects};rows={m.name:topology(m) for m in meshes}
        groups[name]={'objects':len(objects),'unique_meshes':len(meshes),
            'open_objects':sum(rows[o.data.name]['nonmanifold_edges']>0 for o in objects),'meshes':rows}
    other=[];deps=bpy.context.evaluated_depsgraph_get()
    clay={o for name in GROUPS for o in bpy.data.collections[name].objects}
    for o in bpy.data.collections['05_ROOF'].all_objects:
        if o.type!='MESH' or o in clay:continue
        ev=o.evaluated_get(deps);me=ev.to_mesh();record=topology(me);ev.to_mesh_clear()
        other.append(dict(name=o.name,**record))
    return {'groups':groups,'other_roof_evaluated':other}

def path(mode,version):
    folder='Assembly' if mode=='assembly' else ('Materials' if version=='v011' else 'Roof')
    file='Cottage_Courtyard.blend' if mode=='assembly' else 'House_Cottage_A.blend'
    return ROOT/'Source'/folder/version/file

def repair():
    changed=[];done=set();sources=[]
    for name,thickness in GROUPS.items():
        for o in list(bpy.data.collections[name].objects):
            old=o.data
            if old in done:continue
            done.add(old);info=topology(old)
            if info['nonmanifold_edges']==0:continue
            assert info['wire_edges']==0 and info['boundary_edges']>0,(o.name,info)
            aliases=[a for a in bpy.data.objects if a.type=='MESH' and a.data==old]
            coords=[v.co.copy() for v in old.vertices]
            o.data=old.copy();active(o)
            shell=o.modifiers.new('Restore inward clay thickness','SOLIDIFY')
            shell.thickness=thickness;shell.offset=-1;shell.use_rim=True
            shell.use_even_offset=True
            bpy.ops.object.modifier_apply(modifier=shell.name)
            result=topology(o.data)
            assert result['nonmanifold_edges']==0 and result['volume']>1e-9,(o.name,result)
            # The original surface vertices remain unchanged; thickness is added inward.
            assert len(o.data.vertices)>=len(coords)
            assert all((o.data.vertices[i].co-v).length<1e-6 for i,v in enumerate(coords)),o.name
            for alias in aliases:
                alias.data=o.data;alias['roof_solid_v012']='Restored inward thickness, original outer surface preserved'
                alias['clay_thickness_local_m']=thickness;changed.append(alias.name)
            sources.append({'example':o.name,'instances':len(aliases),'thickness_local_m':thickness,
                'before':info,'after':result})
    return changed,sources

def validate_roof():
    report=audit()
    assert all(g['open_objects']==0 for g in report['groups'].values()),report
    assert all(r['nonmanifold_edges']==0 and r['volume']>1e-9 for r in report['other_roof_evaluated']),report['other_roof_evaluated']
    objs=list(bpy.data.collections['05_ROOF'].all_objects)
    geometry=inspect_geometry(objs);assert not geometry['issues'],geometry
    report['geometry']=geometry
    return report

def build(mode):
    target=path(mode,'v012');assert not target.exists(),target
    bpy.ops.wm.open_mainfile(filepath=str(path(mode,'v011')));bpy.context.view_layer.update()
    before=HELPER['digest'](list(bpy.data.objects));changed,repairs=repair()
    bpy.context.view_layer.update();after=HELPER['digest'](list(bpy.data.objects))
    assert {k:v for k,v in before.items() if k not in changed}=={k:v for k,v in after.items() if k not in changed}
    report=validate_roof();report.update(changed=changed,repairs=repairs,other_geometry_unchanged=True,
        original_outer_vertices_preserved=True,file=str(target.relative_to(ROOT)))
    target.parent.mkdir(parents=True,exist_ok=True);sc=bpy.context.scene
    bpy.ops.wm.save_as_mainfile(filepath=str(target))
    (ROOT/'QA'/('roof_solids_v012_'+mode+'.json')).write_text(json.dumps(report,indent=2),encoding='utf-8')
    if mode=='house':
        render(sc,sc.camera,REND/'House_Hero.png',1000)
        st=bpy.data.collections['90_STUDIO - not exported']
        cam=camera('QA_Roof_Close',(-8,-7,6.3),(-1.3,-.8,3.85),5.0,st)
        render(sc,cam,REND/'Roof_Detail.png',950)
        cam=camera('QA_Roof_Rear',(8,9,7),(0,0,3.0),9.5,st)
        render(sc,cam,REND/'House_Rear.png',900)
    else:render(sc,sc.camera,REND/'Courtyard_Hero.png',1100)
    print('ROOF_SOLIDS_COMPLETE',mode,len(changed),len(repairs),flush=True)

def readback():
    report=[]
    for mode in ['house','assembly']:
        build_report=json.loads((ROOT/'QA'/('roof_solids_v012_'+mode+'.json')).read_text(encoding='utf-8'))
        changed=build_report['changed']
        bpy.ops.wm.open_mainfile(filepath=str(path(mode,'v011')));bpy.context.view_layer.update()
        before=HELPER['digest'](list(bpy.data.objects))
        outer={n:[v.co.copy() for v in bpy.data.objects[n].data.vertices] for n in changed}
        matrices={n:[list(r) for r in bpy.data.objects[n].matrix_world] for n in changed}
        bpy.ops.wm.open_mainfile(filepath=str(path(mode,'v012')));bpy.context.view_layer.update()
        after=HELPER['digest'](list(bpy.data.objects))
        assert {k:v for k,v in before.items() if k not in changed}=={k:v for k,v in after.items() if k not in changed}
        for n,coords in outer.items():
            o=bpy.data.objects[n]
            assert matrices[n]==[list(r) for r in o.matrix_world],n
            assert all((o.data.vertices[i].co-v).length<1e-6 for i,v in enumerate(coords)),n
        result=validate_roof();result.update(name=mode,outer_vertices_preserved=True,other_geometry_unchanged=True)
        report.append(result)
    (ROOT/'QA/roof_solids_v012_readback.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('ROOF_SOLIDS_READBACK_COMPLETE',flush=True)

if __name__=='__main__':
    mode=sys.argv[sys.argv.index('--')+1];REND.mkdir(parents=True,exist_ok=True)
    if mode=='audit':
        bpy.ops.wm.open_mainfile(filepath=str(path('house','v011')))
        data=audit();(ROOT/'QA/roof_solids_v011_audit.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
        print(json.dumps({k:{x:v for x,v in r.items() if x!='meshes'} for k,r in data['groups'].items()}),flush=True)
        print(json.dumps(data['other_roof_evaluated']),flush=True)
    elif mode=='validate':readback()
    else:build(mode)
