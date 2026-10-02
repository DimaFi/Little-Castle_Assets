"""v016: seat ridge skirts on real roof surfaces, then finish paused plaster stage."""
import sys,json,math,runpy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from kit_geometry import *
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
PLASTER=runpy.run_path(str(Path(__file__).with_name('24_plaster_materials.py')),run_name='plaster_helpers')
DIGEST=PLASTER['HELP']['digest']
REND=ROOT/'Renders/Checkpoint_11/v016'

def tree(objects):
    verts=[];faces=[];deps=bpy.context.evaluated_depsgraph_get()
    for o in objects:
        ev=o.evaluated_get(deps);me=ev.to_mesh();offset=len(verts)
        verts.extend(o.matrix_world@v.co for v in me.vertices)
        faces.extend(tuple(offset+i for i in p.vertices) for p in me.polygons);ev.to_mesh_clear()
    return BVHTree.FromPolygons(verts,faces)

def support_trees():
    roof=bpy.data.collections['05_ROOF']
    main=list(bpy.data.collections['ROOF_TILES_MAIN'].objects)
    main += [o for o in roof.objects if o.name.startswith(('SM_Roof_Main_','SM_Roof_Verge_'))]
    dormer=list(bpy.data.collections['ROOF_TILES_DORMER'].objects)+[bpy.data.objects['SM_Dormer_Hood_A']]
    return {'main':tree(main),'dormer':tree(dormer)}

def rims(o):
    # Outer surface preserved by earlier Solidify pass: two rings of 13 vertices.
    return [(o.data.vertices[a].co.copy(),o.data.vertices[b].co.copy()) for a,b in [(0,13),(12,25)]]

def ray(t,p):
    hit,normal,index,distance=t.ray_cast(Vector((p.x,p.y,9)),Vector((0,0,-1)),12)
    return None if hit is None else hit.z

def measure(o,t):
    samples=[]
    for side,(a,b) in enumerate(rims(o)):
        for f in [i/40 for i in range(1,40)]:
            p=o.matrix_world@a.lerp(b,f);z=ray(t,p)
            if z is not None:samples.append({'side':side,'fraction':f,'gap':p.z-z,'support':z})
    return samples

def source(mode,version):
    return ROOT/'Source'/('Assembly' if mode=='assembly' else 'Roof')/version/('Cottage_Courtyard.blend' if mode=='assembly' else 'House_Cottage_A.blend')

def audit():
    trees=support_trees();rows=[]
    for o in bpy.data.collections['ROOF_RIDGE_CAPS'].objects:
        kind='dormer' if 'Dormer' in o.name else 'main';s=measure(o,trees[kind])
        rows.append({'name':o.name,'kind':kind,'samples':s,'max_gap':max((q['gap'] for q in s),default=0)})
    return rows

def seat():
    trees=support_trees();records=[]
    for o in bpy.data.collections['ROOF_RIDGE_CAPS'].objects:
        kind='dormer' if 'Dormer' in o.name else 'main';t=trees[kind]
        before=measure(o,t);assert before,o.name
        # Lower the whole cap modestly, preserving ample crown clearance.
        lower=.060 if kind=='main' else .008
        crown_inner=o.matrix_world@o.data.vertices[32].co
        z=ray(t,crown_inner)
        if z is not None:lower=min(lower,max(0,crown_inner.z-z-.018))
        drops=[]
        for side in [0,1]:
            gaps=[p['gap'] for p in before if p['side']==side]
            if not gaps:gaps=[p['gap'] for p in before]
            drops.append(max(0,max(gaps)-lower+.006))
        o.data=o.data.copy()
        # Extend the skirts smoothly while leaving the crown shape intact.
        # This avoids sinking the crown through the uppermost roof tiles.
        local_z_to_world=o.matrix_world.to_3x3().col[2].z
        for v in o.data.vertices:
            r=math.hypot(v.co.y,v.co.z)
            sine=max(0,min(1,v.co.z/r)) if r else 1
            weight=(1-sine)**2
            side=0 if v.co.y>=0 else 1
            v.co.z-=drops[side]*weight/local_z_to_world
        o.location.z-=lower
        o.data.update();bpy.context.view_layer.update()
        after=measure(o,t);maximum=max(p['gap'] for p in after)
        assert maximum<=.004,(o.name,maximum)
        o['ridge_seating']='v016: crown lowered conservatively, skirts fitted to raycast roof contact'
        o['ridge_lowered_m']=lower;o['ridge_skirt_extension_m']=drops
        records.append({'name':o.name,'kind':kind,'lowered_m':lower,'skirt_extension_m':drops,
                        'max_gap_before_m':max(p['gap'] for p in before),'max_gap_after_m':maximum,
                        'checked_contact_samples':len(after)})
    return records

def closed_caps():
    caps=list(bpy.data.collections['ROOF_RIDGE_CAPS'].objects)
    stats=inspect_geometry(caps);assert not stats['issues'],stats
    for o in caps:
        bm=bmesh.new();bm.from_mesh(o.data)
        assert all(e.is_manifold for e in bm.edges),o.name
        assert abs(bm.calc_volume())>1e-8,o.name
        bm.free()
        o.data.calc_loop_triangles();uv=o.data.uv_layers['UV0'].data
        for tri in o.data.loop_triangles:
            a,b,c=[uv[i].uv for i in tri.loops]
            assert abs((b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x))>1e-12,o.name
    return stats

def build(mode):
    target=source(mode,'v016');assert not target.exists(),target
    bpy.ops.wm.open_mainfile(filepath=str(source(mode,'v014')));bpy.context.view_layer.update()
    before=DIGEST(list(bpy.data.objects));records=seat();plaster=PLASTER['assign']()
    names={r['name'] for r in records};after=DIGEST(list(bpy.data.objects))
    assert {n:v for n,v in before.items() if n not in names}=={n:v for n,v in after.items() if n not in names}
    stats=closed_caps();sc=bpy.context.scene
    target.parent.mkdir(parents=True,exist_ok=True);bpy.ops.wm.save_as_mainfile(filepath=str(target))
    report={'file':str(target.relative_to(ROOT)),'caps':records,'cap_geometry':stats,'plaster':plaster,'other_geometry_unchanged':True}
    (ROOT/'QA'/('ridge_plaster_v016_'+mode+'.json')).write_text(json.dumps(report,indent=2),encoding='utf-8')
    if mode=='house':
        render(sc,sc.camera,REND/'House_Hero.png',1000)
        st=bpy.data.collections['90_STUDIO - not exported']
        cam=camera('QA_Ridge_Close',(-8,-9,6.1),(-1,-.05,5.35),4.3,st);render(sc,cam,REND/'Ridge_Detail.png',1000)
        cam=camera('QA_Reverse',(8,9,7),(0,0,3),9.5,st);render(sc,cam,REND/'House_Rear.png',950)
    else:render(sc,sc.camera,REND/'Courtyard_Hero.png',1100)
    print('RIDGE_PLASTER_COMPLETE',mode,flush=True)

def readback():
    reports=[]
    for mode in ['house','assembly']:
        bpy.ops.wm.open_mainfile(filepath=str(source(mode,'v014')));bpy.context.view_layer.update()
        before=DIGEST(list(bpy.data.objects));names={o.name for o in bpy.data.collections['ROOF_RIDGE_CAPS'].objects}
        bpy.ops.wm.open_mainfile(filepath=str(source(mode,'v016')));bpy.context.view_layer.update()
        after=DIGEST(list(bpy.data.objects))
        assert {n:v for n,v in before.items() if n not in names}=={n:v for n,v in after.items() if n not in names}
        caps=closed_caps();contacts=audit();assert max(r['max_gap'] for r in contacts)<=.004
        plaster=PLASTER['verify'](PLASTER['targets']())
        images=[n.image for n in bpy.data.materials['M_Cottage_WarmPlaster_A'].node_tree.nodes if n.type=='TEX_IMAGE']
        assert len(images)==3 and all(i.packed_file for i in images)
        assert bpy.context.scene.camera
        reports.append({'name':mode,'caps':caps,'max_contact_gap_m':max(r['max_gap'] for r in contacts),
                        'contact_samples':sum(len(r['samples']) for r in contacts),'plaster':plaster,
                        'packed_plaster_images':3,'other_geometry_unchanged':True})
    (ROOT/'QA/ridge_plaster_v016_readback.json').write_text(json.dumps(reports,indent=2),encoding='utf-8')
    print('RIDGE_PLASTER_READBACK_COMPLETE',flush=True)

def preview():
    bpy.ops.wm.open_mainfile(filepath=str(source('house','v014')));bpy.context.view_layer.update()
    records=seat();PLASTER['assign']();closed_caps()
    sc=bpy.context.scene;render(sc,sc.camera,REND/'Preview.png',750)
    print(json.dumps(records),flush=True)

def checker():
    bpy.ops.wm.open_mainfile(filepath=str(source('house','v016')));sc=bpy.context.scene
    m=bpy.data.materials.new('QA_Plaster_Checker');m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links
    uv=n.new('ShaderNodeUVMap');uv.uv_map='UV0';tex=n.new('ShaderNodeTexChecker');tex.inputs['Scale'].default_value=10
    tex.inputs['Color1'].default_value=(.025,.09,.16,1);tex.inputs['Color2'].default_value=(.65,.8,.8,1)
    l.new(uv.outputs[0],tex.inputs['Vector']);l.new(tex.outputs[0],n.get('Principled BSDF').inputs['Base Color'])
    for o in PLASTER['targets']():o.data.materials[0]=m
    render(sc,sc.camera,REND/'Plaster_UV_Check.png',950)

if __name__=='__main__':
    mode=sys.argv[sys.argv.index('--')+1];REND.mkdir(parents=True,exist_ok=True)
    if mode=='audit':
        bpy.ops.wm.open_mainfile(filepath=str(source('house','v014')));bpy.context.view_layer.update()
        report=audit();(ROOT/'QA/ridge_v014_contact.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        print(json.dumps([{'name':r['name'],'max_gap':round(r['max_gap'],4),'samples':len(r['samples'])} for r in report]),flush=True)
    elif mode=='preview':preview()
    elif mode=='validate':readback()
    elif mode=='checker':checker()
    else:build(mode)
