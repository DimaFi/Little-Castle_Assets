"""v015: plaster UV/materials. Blender -- [preview|house|assembly|checker|validate]."""
import sys,json,math,runpy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from kit_geometry import *
ROOT=Path(__file__).resolve().parents[1];MAT=ROOT.parents[1]/'Mat/T_Plaster'
REND=ROOT/'Renders/Checkpoint_10/v015';SCALE=.43
HELP=runpy.run_path(str(Path(__file__).with_name('16_timber_materials.py')),run_name='helpers')

def targets():
    return list(bpy.data.collections['03_WALLS'].all_objects)+[o for o in bpy.data.collections['05_ROOF'].objects if o.name.startswith(('SM_Dormer_Front_A','SM_Dormer_Cheek_A'))]

def material():
    m=bpy.data.materials.new('M_Cottage_WarmPlaster_A');m.use_nodes=True;m.diffuse_color=(.50,.37,.22,1)
    n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF');p.location=(650,100)
    uv=n.new('ShaderNodeUVMap');uv.uv_map='UV0';uv.location=(-650,0)
    for i,channel in enumerate(['BaseColor','Roughness','Normal']):
        im=bpy.data.images.load(str(MAT/('T_Plaster_A_'+channel+'.png')),check_existing=True)
        im.colorspace_settings.name='sRGB' if channel=='BaseColor' else 'Non-Color';im.pack()
        tex=n.new('ShaderNodeTexImage');tex.image=im;tex.location=(-420,320-i*320)
        l.new(uv.outputs[0],tex.inputs['Vector'])
        if channel=='BaseColor':
            mix=n.new('ShaderNodeMixRGB');mix.inputs[0].default_value=.55;mix.inputs[2].default_value=(.50,.37,.22,1)
            mix.label='Warm lime plaster; soften source flaking';mix.location=(50,300)
            l.new(tex.outputs['Color'],mix.inputs[1]);l.new(mix.outputs[0],p.inputs['Base Color'])
        elif channel=='Roughness':
            r=n.new('ShaderNodeMapRange');r.inputs['To Min'].default_value=.78;r.inputs['To Max'].default_value=.96;r.location=(50,0)
            l.new(tex.outputs[0],r.inputs['Value']);l.new(r.outputs[0],p.inputs['Roughness'])
        else:
            normal=n.new('ShaderNodeNormalMap');normal.uv_map='UV0';normal.inputs['Strength'].default_value=.055;normal.location=(50,-260)
            l.new(tex.outputs[0],normal.inputs['Color']);l.new(normal.outputs[0],p.inputs['Normal'])
    m['source']='CozySettlement/Mat/T_Plaster; original packed BaseColor/Roughness/Normal'
    m['uv_note']='World-metric face projection into UV0 at .43 UV/m; repeatable, overlapping, not lightmap.'
    return m

def unwrap(o):
    me=o.data;uv=me.uv_layers.get('UV0') or me.uv_layers.new(name='UV0')
    matrix=o.matrix_world;normal_matrix=matrix.to_3x3().inverted().transposed()
    for p in me.polygons:
        normal=normal_matrix@p.normal;drop=max(range(3),key=lambda i:abs(normal[i]))
        axes=[i for i in range(3) if i!=drop]
        for li in p.loop_indices:
            co=matrix@me.vertices[me.loops[li].vertex_index].co
            uv.data[li].uv=(co[axes[0]]*SCALE+.17,co[axes[1]]*SCALE+.11)
    o['stage']='PLASTER v015; UV0 and packed maps; no lightmap/LOD'
    o['uv_method']='World-metric projection, plane selected per base face'
    o['uv_scale_per_m']=SCALE

def verify(objects):
    stats=inspect_geometry(objects);assert not stats['issues'],stats
    count=0
    for o in objects:
        me=o.data;assert me.materials[0].name=='M_Cottage_WarmPlaster_A',o.name
        me.calc_loop_triangles();uv=me.uv_layers['UV0'].data
        for t in me.loop_triangles:
            a,b,c=[uv[li].uv for li in t.loops]
            area=abs((b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x))/2
            assert math.isfinite(area) and area>1e-12,(o.name,'Collapsed base UV')
            count+=1
    stats.update(base_uv_triangles_checked=count,base_uv_degenerate_faces=0,names=[o.name for o in objects])
    return stats

def assign():
    mat=material();objects=targets()
    for o in objects:
        assert o.type=='MESH',o.name
        o.data=o.data.copy();o.data.materials.clear();o.data.materials.append(mat)
        for p in o.data.polygons:p.material_index=0
        unwrap(o)
    return verify(objects)

def path(mode,version):
    folder='Assembly' if mode=='assembly' else ('Roof' if version=='v014' else 'Materials')
    return ROOT/'Source'/folder/version/('Cottage_Courtyard.blend' if mode=='assembly' else 'House_Cottage_A.blend')

def build(mode):
    kind='house' if mode=='preview' else mode;target=path(kind,'v015')
    if mode!='preview':assert not target.exists(),target
    bpy.ops.wm.open_mainfile(filepath=str(path(kind,'v014')));bpy.context.view_layer.update()
    before=HELP['digest'](list(bpy.data.objects));stats=assign()
    assert before==HELP['digest'](list(bpy.data.objects))
    sc=bpy.context.scene
    if mode=='preview':
        render(sc,sc.camera,REND/'Plaster_Preview.png',750);return
    target.parent.mkdir(parents=True,exist_ok=True);bpy.ops.wm.save_as_mainfile(filepath=str(target))
    stats.update(file=str(target.relative_to(ROOT)),geometry_and_pivots_unchanged=True)
    (ROOT/'QA'/('plaster_v015_'+mode+'.json')).write_text(json.dumps(stats,indent=2),encoding='utf-8')
    if mode=='house':
        render(sc,sc.camera,REND/'House_Hero.png',1000)
        st=bpy.data.collections['90_STUDIO - not exported']
        cam=camera('QA_Plaster_Detail',(-5,-7,3.6),(-.65,-2.3,2.5),4.1,st);render(sc,cam,REND/'Plaster_Detail.png',950)
        cam=camera('QA_Plaster_Rear',(8,9,7),(0,0,3),9.5,st);render(sc,cam,REND/'House_Rear.png',950)
    else:render(sc,sc.camera,REND/'Courtyard_Hero.png',1100)
    print('PLASTER_COMPLETE',mode,stats['objects'],flush=True)

def checker():
    bpy.ops.wm.open_mainfile(filepath=str(path('house','v015')));sc=bpy.context.scene
    m=bpy.data.materials.new('QA_Plaster_Checker');m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links
    uv=n.new('ShaderNodeUVMap');uv.uv_map='UV0';tex=n.new('ShaderNodeTexChecker');tex.inputs['Scale'].default_value=10
    tex.inputs['Color1'].default_value=(.025,.09,.16,1);tex.inputs['Color2'].default_value=(.65,.8,.8,1)
    l.new(uv.outputs[0],tex.inputs['Vector']);l.new(tex.outputs[0],n.get('Principled BSDF').inputs['Base Color'])
    for o in targets():o.data.materials[0]=m
    render(sc,sc.camera,REND/'Plaster_UV_Check.png',950)

def readback():
    report=[]
    for mode in ['house','assembly']:
        bpy.ops.wm.open_mainfile(filepath=str(path(mode,'v014')));bpy.context.view_layer.update()
        before=HELP['digest'](list(bpy.data.objects))
        bpy.ops.wm.open_mainfile(filepath=str(path(mode,'v015')));bpy.context.view_layer.update()
        assert before==HELP['digest'](list(bpy.data.objects)),mode
        stats=verify(targets())
        images=[n.image for n in bpy.data.materials['M_Cottage_WarmPlaster_A'].node_tree.nodes if n.type=='TEX_IMAGE']
        assert len(images)==3 and all(im.packed_file for im in images)
        assert bpy.context.scene.camera
        stats.update(name=mode,geometry_and_pivots_unchanged=True,packed_images=3,camera_saved=True);report.append(stats)
    (ROOT/'QA/plaster_v015_readback.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('PLASTER_READBACK_COMPLETE',flush=True)

if __name__=='__main__':
    REND.mkdir(parents=True,exist_ok=True);mode=sys.argv[sys.argv.index('--')+1]
    if mode=='validate':readback()
    elif mode=='checker':checker()
    else:build(mode)
