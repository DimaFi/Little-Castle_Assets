"""Materials for woodshed and logs; v019 assembly, Yard/v003 gallery/modules.
Blender -- [preview|assembly|gallery|modules|validate]. Preserve previous versions.
"""
import sys,json,math,runpy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from kit_geometry import *
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1];REND=ROOT/'Renders/Checkpoint_14/v019'
NAMES=['SM_Woodshed_A','SM_LogStack_A']
TIMBER=runpy.run_path(str(Path(__file__).with_name('16_timber_materials.py')),run_name='helpers')
ROOF=runpy.run_path(str(Path(__file__).with_name('22_roof_materials.py')),run_name='helpers')
STONE=runpy.run_path(str(Path(__file__).with_name('27_masonry_materials.py')),run_name='helpers')
ASSEMBLY=ROOT/'Source/Assembly/v019/Cottage_Courtyard.blend'
YARD=ROOT/'Source/Yard/v003'

def parts():return [o for name in NAMES for o in bpy.data.collections[name].all_objects if o.type=='MESH']

def load_materials():
    names=['M_Cottage_StructuralTimber_A','M_Cottage_FrameWood_A','M_Cottage_Terracotta_A','M_Cottage_RoofUnderlay_A','M_Cottage_FieldStone_A']
    missing=[n for n in names if n not in bpy.data.materials]
    if missing:
        with bpy.data.libraries.load(str(ROOT/'Source/Roof/v018/House_Cottage_A.blend'),link=False) as (src,dst):dst.materials=missing
    if 'M_Oak_Bark' not in bpy.data.materials:
        with bpy.data.libraries.load(str(ROOT.parent/'Vegetation/Oak_Kit/Cozy_Oak_Kit.blend'),link=False) as (src,dst):dst.materials=['M_Oak_Bark']
    bark=bpy.data.materials['M_Oak_Bark'].copy();bark.name='M_Cottage_LogBark_A'
    for node in bark.node_tree.nodes:
        if node.type=='NORMAL_MAP':node.inputs['Strength'].default_value=.16
    m=bpy.data.materials.new('M_Cottage_LogEndGrain_A');m.use_nodes=True;m.diffuse_color=(.48,.275,.12,1)
    n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF');p.inputs['Roughness'].default_value=.86
    uv=n.new('ShaderNodeUVMap');uv.uv_map='UV0'
    shift=n.new('ShaderNodeVectorMath');shift.operation='SUBTRACT';shift.inputs[1].default_value=(.5,.5,0)
    l.new(uv.outputs[0],shift.inputs[0])
    wave=n.new('ShaderNodeTexWave');wave.wave_type='RINGS';wave.rings_direction='Z';wave.wave_profile='SIN'
    wave.inputs['Scale'].default_value=5.5;wave.inputs['Distortion'].default_value=2.0;wave.inputs['Detail Scale'].default_value=1.7
    info=n.new('ShaderNodeObjectInfo');variation=n.new('ShaderNodeMapRange')
    variation.inputs['To Min'].default_value=4.2;variation.inputs['To Max'].default_value=6.0
    l.new(info.outputs['Random'],variation.inputs['Value']);l.new(variation.outputs[0],wave.inputs['Scale'])
    l.new(shift.outputs[0],wave.inputs['Vector'])
    ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.24;ramp.color_ramp.elements[0].color=(.30,.16,.065,1)
    ramp.color_ramp.elements[1].position=.52;ramp.color_ramp.elements[1].color=(.54,.34,.16,1)
    l.new(wave.outputs['Color'],ramp.inputs[0]);l.new(ramp.outputs[0],p.inputs['Base Color'])
    m['note']='Procedural annual rings on planar cut ends; bake to texture before game export.'
    for mat in list(bpy.data.materials):
        if mat.use_nodes:
            for node in mat.node_tree.nodes:
                if node.type=='TEX_IMAGE' and node.image and not node.image.packed_file:node.image.pack()

def assign_one(o,names):
    o.data=o.data.copy();o.data.materials.clear()
    for name in names:o.data.materials.append(bpy.data.materials[name])
    for p in o.data.polygons:p.material_index=0
    o['material_stage']='Yard batch 1 v019; UV0/materials, not lightmap/export'

def board_uv(o):
    me=o.data;coords=[v.co for v in me.vertices];span=[max(v[i] for v in coords)-min(v[i] for v in coords) for i in range(3)]
    long=max(range(3),key=lambda i:span[i]);uv=me.uv_layers.get('UV0') or me.uv_layers.new(name='UV0')
    for p in me.polygons:
        drop=max(range(3),key=lambda i:abs(p.normal[i]));axes=[i for i in range(3) if i!=drop]
        if long in axes:axes=[long,next(i for i in axes if i!=long)]
        for li in p.loop_indices:
            v=me.vertices[me.loops[li].vertex_index].co
            uv.data[li].uv=(.11+v[axes[0]]*.43,.17+v[axes[1]]*.43)

def log_uv(o):
    me=o.data;uv=me.uv_layers.get('UV0') or me.uv_layers.new(name='UV0')
    assert len(me.vertices)==44,o.name
    centers=[sum((me.vertices[j*11+i].co for i in range(11)),Vector())/11 for j in range(4)]
    radius=max((me.vertices[i].co-centers[0]).length for i in range(11))
    for p in me.polygons:
        rings={me.loops[li].vertex_index//11 for li in p.loop_indices}
        if len(rings)==1:
            p.material_index=1;c=centers[next(iter(rings))]
            for li in p.loop_indices:
                v=me.vertices[me.loops[li].vertex_index].co-c;uv.data[li].uv=(.5+v.x/(2*radius),.5+v.z/(2*radius))
        else:
            seam={me.loops[li].vertex_index%11 for li in p.loop_indices}=={0,10}
            for li in p.loop_indices:
                idx=me.loops[li].vertex_index;ring=idx//11;c=idx%11
                uv.data[li].uv=((11 if seam and c==0 else c)/11*2,(centers[ring]-centers[0]).length)

def end_uv(o):
    me=o.data;uv=me.uv_layers.get('UV0') or me.uv_layers.new(name='UV0');r=max(math.hypot(v.co.x,v.co.y) for v in me.vertices)
    for p in me.polygons:
        for li in p.loop_indices:
            v=me.vertices[me.loops[li].vertex_index].co
            if abs(p.normal.z)>.5:uv.data[li].uv=(.5+v.x/(2*r),.5+v.y/(2*r))
            else:
                # Axial strip for the thin edge, avoiding collapsed side UVs.
                a=math.atan2(v.y,v.x)
                angles=[math.atan2(me.vertices[me.loops[i].vertex_index].co.y,me.vertices[me.loops[i].vertex_index].co.x) for i in p.loop_indices]
                if max(angles)-min(angles)>math.pi and a<0:a+=2*math.pi
                uv.data[li].uv=(a/(2*math.pi),v.z/(2*r))

def solidify(o,thickness):
    info=ROOF['HELP']['topology'](o.data)
    if not info['nonmanifold_edges']:return False
    active(o);m=o.modifiers.new('Restore inward clay thickness','SOLIDIFY');m.thickness=thickness;m.offset=-1;m.use_even_offset=True
    bpy.ops.object.modifier_apply(modifier=m.name)
    assert ROOF['HELP']['topology'](o.data)['nonmanifold_edges']==0,o.name
    return True

def seat_caps(objects):
    verts=[];faces=[];deps=bpy.context.evaluated_depsgraph_get()
    for o in objects:
        if not o.name.startswith(('Roof_Tile','Roof_Shell')):continue
        ev=o.evaluated_get(deps);me=ev.to_mesh();offset=len(verts)
        verts.extend(o.matrix_world@v.co for v in me.vertices);faces.extend(tuple(offset+i for i in p.vertices) for p in me.polygons);ev.to_mesh_clear()
    tree=BVHTree.FromPolygons(verts,faces);records=[]
    for o in objects:
        if not o.name.startswith('Roof_RidgeCap'):continue
        drops=[]
        for a,b in [(0,13),(12,25)]:
            gaps=[]
            for j in range(1,20):
                p=o.matrix_world@o.data.vertices[a].co.lerp(o.data.vertices[b].co,j/20)
                hit,_,_,_=tree.ray_cast(Vector((p.x,p.y,6)),Vector((0,0,-1)),8)
                if hit is not None:gaps.append(p.z-hit.z)
            assert gaps,o.name
            drops.append(max(0,max(gaps)+.004))
        for v in o.data.vertices:
            r=math.hypot(v.co.y,v.co.z);s=max(0,min(1,v.co.z/r)) if r else 1
            v.co.z-=drops[0 if v.co.y>=0 else 1]*(1-s)**2/o.scale.z
        o.data.update();records.append({'name':o.name,'skirt_extension_world_m':drops})
    return records

def apply():
    load_materials();objects=parts();before=TIMBER['digest'](list(bpy.data.objects));geometry_changed=[]
    # Source collections live in a separate scene; select it for modifiers/depsgraph.
    original=bpy.context.scene
    scene=bpy.data.scenes.new('TEMP_Yard_Material_Evaluation')
    for name in NAMES:scene.collection.children.link(bpy.data.collections[name])
    bpy.context.window.scene=scene;bpy.context.view_layer.update()
    for o in objects:
        name=o.name
        if name.startswith('Log_Bark'):
            assign_one(o,['M_Cottage_LogBark_A','M_Cottage_LogEndGrain_A']);log_uv(o)
        elif name.startswith('Log_CutEnd'):
            assign_one(o,['M_Cottage_LogEndGrain_A']);end_uv(o)
        elif name.startswith('Roof_RidgeCap'):
            assign_one(o,['M_Cottage_Terracotta_A']);solidify(o,.04);geometry_changed.append(name)
            ROOF['unwrap'](o.data,'ROOF_RIDGE_CAPS')
        elif name.startswith('Roof_Tile'):
            assign_one(o,['M_Cottage_Terracotta_A'])
            if solidify(o,.035):geometry_changed.append(name)
            ROOF['unwrap'](o.data,'ROOF_TILES_MAIN')
        elif name.startswith('Roof_Shell'):
            assign_one(o,['M_Cottage_RoofUnderlay_A']);board_uv(o)
        elif name.startswith('Stone_Foot'):
            assign_one(o,['M_Cottage_FieldStone_A']);STONE['unwrap'](o,'field')
        elif name.startswith(('Back_Board','Side_Board')):
            assign_one(o,['M_Cottage_FrameWood_A']);board_uv(o)
        else:
            assign_one(o,['M_Cottage_StructuralTimber_A']);TIMBER['unwrap'](o)
    bpy.context.view_layer.update();caps=seat_caps(objects)
    after=TIMBER['digest'](list(bpy.data.objects));ex=set(geometry_changed)
    assert {n:v for n,v in before.items() if n not in ex}=={n:v for n,v in after.items() if n not in ex}
    stats=verify(objects);bpy.context.window.scene=original;bpy.data.scenes.remove(scene)
    return dict(stats=stats,geometry_changed=geometry_changed,cap_seating=caps,other_geometry_unchanged=True)

def verify(objects):
    stats=inspect_geometry(objects);assert not stats['issues'],stats
    count=0
    for o in objects:
        assert o.data.materials and all(m and m.name!='M_Blockout_Grey' for m in o.data.materials),o.name
        me=o.data;me.calc_loop_triangles();uv=me.uv_layers['UV0'].data
        for t in me.loop_triangles:
            a,b,c=[uv[i].uv for i in t.loops]
            assert abs((b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x))>1e-12,(o.name,'collapsed UV')
            count+=1
        if o.name.startswith(('Roof_Tile','Roof_RidgeCap')):assert ROOF['HELP']['topology'](me)['nonmanifold_edges']==0,o.name
    stats['uv_triangles_checked']=count;return stats

def view_module(name,filename):
    sc=bpy.data.scenes.new('QA_'+name);sc.unit_settings.system='METRIC';sc.unit_settings.scale_length=1
    sc.collection.children.link(bpy.data.collections[name]);bpy.context.window.scene=sc
    sc.render.engine='CYCLES';sc.cycles.samples=24;sc.cycles.use_denoising=True;sc.render.threads_mode='FIXED';sc.render.threads=8;sc.view_settings.view_transform='AgX'
    st=studio(sc,bpy.data.materials['M_Blockout_Grey'])
    next(o for o in st.objects if o.name.startswith('Studio ground')).location.z=-.125
    lo,hi=bounds(list(bpy.data.collections[name].objects));target=Vector([(lo[i]+hi[i])/2 for i in range(3)])
    cam=camera('CAM_'+name,target+Vector((4,-6,3)),target,max(hi[i]-lo[i] for i in range(3))*1.55,st);sc.camera=cam
    render(sc,cam,REND/filename,950);return sc

def build(mode):
    gallery=mode=='gallery';target=YARD/'Cottage_Yard_Kit.blend' if gallery else ASSEMBLY
    if mode!='preview':assert not target.exists(),target
    source=ROOT/'Source/Yard/v002/Cottage_Yard_Kit.blend' if gallery else ROOT/'Source/Assembly/v018/Cottage_Courtyard.blend'
    bpy.ops.wm.open_mainfile(filepath=str(source));report=apply();sc=bpy.context.scene
    if mode=='preview':
        view_module(NAMES[0],'Preview_Woodshed.png');view_module(NAMES[1],'Preview_Logs.png');print('YARD_PREVIEW_COMPLETE',flush=True);return
    for o in bpy.data.objects:
        if o.instance_type=='COLLECTION' and o.instance_collection and o.instance_collection.name in NAMES:
            o['source_file']='Source/Yard/v003/Modules/'+o.instance_collection.name+'/'+o.instance_collection.name+'.blend'
    target.parent.mkdir(parents=True,exist_ok=True);bpy.ops.wm.save_as_mainfile(filepath=str(target))
    (ROOT/'QA'/('yard_materials_v019_'+mode+'.json')).write_text(json.dumps(report,indent=2),encoding='utf-8')
    render(sc,sc.camera,REND/('Yard_Gallery.png' if gallery else 'Courtyard_Hero.png'),1100)
    print('YARD_MATERIALS_COMPLETE',mode,flush=True)

def modules():
    for name in NAMES:
        target=YARD/'Modules'/name/(name+'.blend');assert not target.exists(),target
        bpy.ops.wm.open_mainfile(filepath=str(ASSEMBLY));sc=view_module(name,name+'.png');sc.name=name+'_Material_v001'
        tmp=ROOT/'QA'/(name+'_library_build.blend');bpy.data.libraries.write(str(tmp),{sc},fake_user=True)
        bpy.ops.wm.open_mainfile(filepath=str(tmp));bpy.context.window.scene=bpy.data.scenes[name+'_Material_v001']
        target.parent.mkdir(parents=True,exist_ok=True);bpy.ops.wm.save_as_mainfile(filepath=str(target));tmp.unlink()
    print('YARD_MODULES_COMPLETE',flush=True)

def validate():
    reports=[]
    files=[('assembly',ASSEMBLY),('gallery',YARD/'Cottage_Yard_Kit.blend')]+[(n,YARD/'Modules'/n/(n+'.blend')) for n in NAMES]
    for label,path in files:
        if label in ['assembly','gallery']:
            previous=ROOT/('Source/Assembly/v018/Cottage_Courtyard.blend' if label=='assembly' else 'Source/Yard/v002/Cottage_Yard_Kit.blend')
            bpy.ops.wm.open_mainfile(filepath=str(previous));bpy.context.view_layer.update();before=TIMBER['digest'](list(bpy.data.objects))
        bpy.ops.wm.open_mainfile(filepath=str(path));objects=parts() if label in ['assembly','gallery'] else list(bpy.data.collections[label].objects)
        if label in ['assembly','gallery']:
            bpy.context.view_layer.update();after=TIMBER['digest'](list(bpy.data.objects))
            excluded=set(json.loads((ROOT/'QA'/('yard_materials_v019_'+label+'.json')).read_text(encoding='utf-8'))['geometry_changed'])
            assert {n:v for n,v in before.items() if n not in excluded}=={n:v for n,v in after.items() if n not in excluded}
        original=bpy.context.scene
        if label in ['assembly','gallery']:
            # Gallery keeps modules in separate scenes: evaluate each independently.
            checks=[]
            for name in NAMES:
                group=list(bpy.data.collections[name].objects)
                scene=next(sc for sc in bpy.data.scenes if all(o.name in sc.objects for o in group));bpy.context.window.scene=scene
                checks.append(verify(group))
        else:checks=[verify(objects)]
        for o in objects:
            for m in o.data.materials:
                if m.use_nodes:
                    for n in m.node_tree.nodes:
                        if n.type=='TEX_IMAGE':assert n.image.packed_file,(label,n.image.name)
        assert original.camera
        reports.append({'file':str(path.relative_to(ROOT)),'checks':checks,'packed_images':True,'saved_camera':True})
    (ROOT/'QA/yard_materials_v019_readback.json').write_text(json.dumps(reports,indent=2),encoding='utf-8')
    print('YARD_READBACK_COMPLETE',flush=True)

if __name__=='__main__':
    REND.mkdir(parents=True,exist_ok=True);mode=sys.argv[sys.argv.index('--')+1]
    if mode=='modules':modules()
    elif mode=='validate':validate()
    else:build(mode)
