"""Reuse catalogue well/bucket geometry and house materials. Assembly v020, Yard v004.
Blender -- preview|assembly|gallery|modules|validate|rope_library
"""
import sys,json,math,runpy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from kit_geometry import *
H=runpy.run_path(str(Path(__file__).with_name('31_yard_materials_batch1.py')),run_name='helpers')
ROOT=Path(__file__).resolve().parents[1];REND=ROOT/'Renders/Checkpoint_15/v020'
NAMES=['SM_Well_A','SM_Bucket_A'];ASSEMBLY=ROOT/'Source/Assembly/v020/Cottage_Courtyard.blend';YARD=ROOT/'Source/Yard/v004'
for key,value in [('NAMES',NAMES),('REND',REND),('ASSEMBLY',ASSEMBLY),('YARD',YARD)]:H['parts'].__globals__[key]=value
TIMBER=H['TIMBER'];ROOF=H['ROOF'];STONE=H['STONE']

def rope_material():
    m=bpy.data.materials.new('M_Cottage_HempRope_A');m.use_nodes=True;m.diffuse_color=(.34,.23,.12,1)
    n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF');p.inputs['Roughness'].default_value=.94
    uv=n.new('ShaderNodeUVMap');uv.uv_map='UV0';uv.location=(-650,0)
    wave=n.new('ShaderNodeTexWave');wave.wave_type='BANDS';wave.bands_direction='DIAGONAL';wave.inputs['Scale'].default_value=32
    wave.inputs['Distortion'].default_value=1.5;wave.location=(-400,100);l.new(uv.outputs[0],wave.inputs['Vector'])
    ramp=n.new('ShaderNodeValToRGB');ramp.location=(-100,180)
    ramp.color_ramp.elements[0].color=(.19,.115,.052,1);ramp.color_ramp.elements[1].color=(.39,.265,.135,1)
    l.new(wave.outputs['Color'],ramp.inputs[0]);l.new(ramp.outputs[0],p.inputs['Base Color'])
    bump=n.new('ShaderNodeBump');bump.location=(140,-120);bump.inputs['Strength'].default_value=.12;bump.inputs['Distance'].default_value=.0006
    l.new(wave.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs[0],p.inputs['Normal'])
    m['asset_book_id']='MAT_Cottage_HempRope_A';m['note']='UV0 metric fiber pattern; procedural, bake before game export. No displacement.'

def cylinder_uv(o,cutends=False):
    me=o.data;uv=me.uv_layers.get('UV0') or me.uv_layers.new(name='UV0');r=max(math.hypot(v.co.x,v.co.y) for v in me.vertices)
    for p in me.polygons:
        cap=abs(p.normal.z)>.7
        if cap and cutends:p.material_index=1
        angles=[math.atan2(me.vertices[me.loops[i].vertex_index].co.y,me.vertices[me.loops[i].vertex_index].co.x) for i in p.loop_indices]
        seam=max(angles)-min(angles)>math.pi
        for li,a in zip(p.loop_indices,angles):
            v=me.vertices[me.loops[li].vertex_index].co
            if cap:uv.data[li].uv=(.5+v.x/(2*r),.5+v.y/(2*r))
            else:
                if seam and a<0:a+=2*math.pi
                uv.data[li].uv=(.1+v.z*.43,.15+a*r*.43)

def tube_uv(o,sides):
    me=o.data;count=len(me.vertices)//sides;assert count*sides==len(me.vertices)
    uv=me.uv_layers.get('UV0') or me.uv_layers.new(name='UV0')
    centers=[sum((me.vertices[j*sides+i].co for i in range(sides)),Vector())/sides for j in range(count)]
    length=[0.]
    for j in range(1,count):length.append(length[-1]+(centers[j]-centers[j-1]).length)
    r=(me.vertices[0].co-centers[0]).length
    for p in me.polygons:
        rings={me.loops[li].vertex_index//sides for li in p.loop_indices}
        corners={me.loops[li].vertex_index%sides for li in p.loop_indices}
        if len(rings)==1:
            j=next(iter(rings));c=centers[j];a=(me.vertices[j*sides].co-c).normalized()
            axis=(centers[min(count-1,j+1)]-centers[max(0,j-1)]).normalized();b=axis.cross(a).normalized()
            for li in p.loop_indices:
                v=me.vertices[me.loops[li].vertex_index].co-c;uv.data[li].uv=(v.dot(a),v.dot(b))
        else:
            seam=corners=={0,sides-1}
            for li in p.loop_indices:
                idx=me.loops[li].vertex_index;j=idx//sides;i=idx%sides
                uv.data[li].uv=(length[j],(sides if seam and i==0 else i)/sides*2*math.pi*r)

def apply():
    if 'M_Cottage_ForgedIron_A' not in bpy.data.materials:
        with bpy.data.libraries.load(str(ROOT/'Source/Roof/v018/House_Cottage_A.blend'),link=False) as (src,dst):dst.materials=['M_Cottage_ForgedIron_A']
    rope_material();objects=H['parts']();before=TIMBER['digest'](list(bpy.data.objects));changed=[]
    original=bpy.context.scene;scene=bpy.data.scenes.new('TEMP_Well_Materials')
    for name in NAMES:scene.collection.children.link(bpy.data.collections[name])
    bpy.context.window.scene=scene;bpy.context.view_layer.update()
    for o in objects:
        name=o.name
        if name.startswith('Well_Stone'):
            H['assign_one'](o,['M_Cottage_FieldStone_A']);STONE['unwrap'](o,'field')
        elif name.startswith('Roof_RidgeCap'):
            H['assign_one'](o,['M_Cottage_Terracotta_A']);H['solidify'](o,.04);changed.append(name);ROOF['unwrap'](o.data,'ROOF_RIDGE_CAPS')
        elif name.startswith('Roof_Tile'):
            H['assign_one'](o,['M_Cottage_Terracotta_A'])
            if H['solidify'](o,.035):changed.append(name)
            ROOF['unwrap'](o.data,'ROOF_TILES_MAIN')
        elif name.startswith('Roof_Shell'):
            H['assign_one'](o,['M_Cottage_RoofUnderlay_A']);H['board_uv'](o)
        elif name.startswith(('Bucket_Hoop','Bucket_Handle')):
            H['assign_one'](o,['M_Cottage_ForgedIron_A']);H['board_uv'](o)
            if name.startswith('Bucket_Handle'):
                o.scale.x*=.90;o.location.z-=.025;changed.append(name)
                o['handle_seating']='v020: ends seated into upper metal hoop'
        elif name.startswith('Rope_Winding'):
            H['assign_one'](o,['M_Cottage_HempRope_A']);tube_uv(o,6)
        elif name.startswith('Well_Rope'):
            H['assign_one'](o,['M_Cottage_HempRope_A']);cylinder_uv(o)
        elif name.startswith(('Windlass','Crank_Grip')):
            H['assign_one'](o,['M_Cottage_FrameWood_A','M_Cottage_LogEndGrain_A']);cylinder_uv(o,True)
        elif name.startswith('Bucket_Floor'):
            H['assign_one'](o,['M_Cottage_FrameWood_A']);cylinder_uv(o)
        elif name.startswith('Bucket_Stave'):
            H['assign_one'](o,['M_Cottage_FrameWood_A']);H['board_uv'](o)
        else:
            H['assign_one'](o,['M_Cottage_StructuralTimber_A']);TIMBER['unwrap'](o)
        o['asset_book_id']='PROP_Bucket_A' if o in bpy.data.collections['SM_Bucket_A'].objects.values() else 'PROP_Well_A'
        o['material_stage']='Well/bucket v020; Asset Book reuse pass'
    bpy.context.view_layer.update();caps=H['seat_caps'](objects);stats=H['verify'](objects)
    after=TIMBER['digest'](list(bpy.data.objects));ex=set(changed)
    assert {n:v for n,v in before.items() if n not in ex}=={n:v for n,v in after.items() if n not in ex}
    bpy.context.window.scene=original;bpy.data.scenes.remove(scene)
    return dict(stats=stats,geometry_changed=changed,cap_seating=caps,other_geometry_unchanged=True)

def build(mode):
    gallery=mode=='gallery';target=YARD/'Cottage_Yard_Kit.blend' if gallery else ASSEMBLY
    if mode!='preview':assert not target.exists(),target
    source=ROOT/('Source/Yard/v003/Cottage_Yard_Kit.blend' if gallery else 'Source/Assembly/v019/Cottage_Courtyard.blend')
    bpy.ops.wm.open_mainfile(filepath=str(source));report=apply();sc=bpy.context.scene
    if mode=='preview':
        for name in NAMES:H['view_module'](name,'Preview_'+name+'.png')
        print('WELL_PREVIEW_COMPLETE',flush=True);return
    for o in bpy.data.objects:
        if o.instance_type=='COLLECTION' and o.instance_collection and o.instance_collection.name in NAMES:o['source_file']=f'Source/Yard/v004/Modules/{o.instance_collection.name}/{o.instance_collection.name}.blend'
    target.parent.mkdir(parents=True,exist_ok=True);bpy.ops.wm.save_as_mainfile(filepath=str(target))
    (ROOT/'QA'/('well_bucket_v020_'+mode+'.json')).write_text(json.dumps(report,indent=2),encoding='utf-8')
    render(sc,sc.camera,REND/('Yard_Gallery.png' if gallery else 'Courtyard_Hero.png'),1100)
    print('WELL_COMPLETE',mode,flush=True)

def validate():
    reports=[]
    paths=[('assembly',ASSEMBLY),('gallery',YARD/'Cottage_Yard_Kit.blend')]+[(n,YARD/'Modules'/n/(n+'.blend')) for n in NAMES]
    for label,path in paths:
        if label in ['assembly','gallery']:
            previous=ROOT/('Source/Assembly/v019/Cottage_Courtyard.blend' if label=='assembly' else 'Source/Yard/v003/Cottage_Yard_Kit.blend')
            bpy.ops.wm.open_mainfile(filepath=str(previous));bpy.context.view_layer.update();before=TIMBER['digest'](list(bpy.data.objects))
        bpy.ops.wm.open_mainfile(filepath=str(path));bpy.context.view_layer.update();original=bpy.context.scene
        if label in ['assembly','gallery']:
            after=TIMBER['digest'](list(bpy.data.objects));excluded=set(json.loads((ROOT/'QA'/('well_bucket_v020_'+label+'.json')).read_text(encoding='utf-8'))['geometry_changed'])
            assert {n:v for n,v in before.items() if n not in excluded}=={n:v for n,v in after.items() if n not in excluded}
        checks=[]
        for name in NAMES if label in ['assembly','gallery'] else [label]:
            objects=list(bpy.data.collections[name].objects);bpy.context.window.scene=next(sc for sc in bpy.data.scenes if all(o.name in sc.objects for o in objects))
            checks.append(H['verify'](objects))
            for o in objects:
                for m in o.data.materials:
                    if m.use_nodes:
                        for n in m.node_tree.nodes:
                            if n.type=='TEX_IMAGE':assert n.image.packed_file
        assert original.camera
        reports.append(dict(file=str(path.relative_to(ROOT)),checks=checks,packed_images=True,camera_saved=True))
    (ROOT/'QA/well_bucket_v020_readback.json').write_text(json.dumps(reports,indent=2),encoding='utf-8');print('WELL_READBACK_COMPLETE',flush=True)

def rope_library():
    bpy.ops.wm.open_mainfile(filepath=str(ASSEMBLY))
    for folder,file,material in [('Rope_v001','Cottage_HempRope.blend','M_Cottage_HempRope_A'),('Iron_v001','Cottage_ForgedIron.blend','M_Cottage_ForgedIron_A')]:
        target=ROOT/'Source/Materials'/folder/file;assert not target.exists()
        target.parent.mkdir(parents=True,exist_ok=True)
        bpy.data.libraries.write(str(target),{bpy.data.materials[material]},fake_user=True)
    print('ROPE_LIBRARY_COMPLETE',flush=True)

if __name__=='__main__':
    REND.mkdir(parents=True,exist_ok=True);mode=sys.argv[sys.argv.index('--')+1]
    if mode=='modules':H['modules']()
    elif mode=='validate':validate()
    elif mode=='rope_library':rope_library()
    else:build(mode)
