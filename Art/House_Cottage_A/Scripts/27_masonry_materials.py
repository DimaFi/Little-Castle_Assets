"""v017 masonry material pass. Run with Blender -- [audit|preview|house|assembly|validate]."""
import sys, json, math, runpy, hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from kit_geometry import *
ROOT=Path(__file__).resolve().parents[1]
MAT=ROOT.parents[1]/'Mat'
REND=ROOT/'Renders/Checkpoint_12/v017'
HELP=runpy.run_path(str(Path(__file__).with_name('25_seat_ridge_plaster.py')),run_name='helpers')

def source(mode,version):
    return ROOT/'Source'/('Assembly' if mode=='assembly' else 'Roof')/version/('Cottage_Courtyard.blend' if mode=='assembly' else 'House_Cottage_A.blend')

PATCHES={
    'field':[(220,350,340,430),(500,430,625,525),(785,650,900,730)],
    'chimney':[(150,40,345,115),(690,40,835,115),(545,355,705,425)]}

def targets():
    return [o for name in ['02_FOUNDATION','06_CHIMNEY'] for o in bpy.data.collections[name].all_objects
            if o.type=='MESH' and o.name!='SM_Chimney_RoofCollar_A']

def material(kind):
    source_name='T_FieldStone' if kind=='field' else 'T_ChimneyStone'
    m=bpy.data.materials.new('M_Cottage_'+('FieldStone' if kind=='field' else 'ChimneyStone')+'_A')
    m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF');p.location=(800,100)
    tint=(.34,.285,.215,1) if kind=='field' else (.43,.355,.255,1)
    m.diffuse_color=tint
    uv=n.new('ShaderNodeUVMap');uv.uv_map='UV0';uv.location=(-800,100)
    for i,channel in enumerate(['BaseColor','Roughness','Normal']):
        im=bpy.data.images.load(str(MAT/source_name/(source_name+'_A_'+channel+'.png')),check_existing=True)
        im.colorspace_settings.name='sRGB' if channel=='BaseColor' else 'Non-Color';im.pack()
        tex=n.new('ShaderNodeTexImage');tex.image=im;tex.location=(-550,350-i*320)
        l.new(uv.outputs[0],tex.inputs['Vector'])
        if channel=='BaseColor':
            mix=n.new('ShaderNodeMixRGB');mix.location=(-200,350);mix.inputs[0].default_value=.62;mix.inputs[2].default_value=tint
            mix.label='Soften painted highlights; retain source stone grain';l.new(tex.outputs[0],mix.inputs[1])
            info=n.new('ShaderNodeObjectInfo');info.location=(-530,620)
            val=n.new('ShaderNodeMapRange');val.location=(-190,640);val.inputs['To Min'].default_value=.84;val.inputs['To Max'].default_value=1.10
            l.new(info.outputs['Random'],val.inputs['Value'])
            mul=n.new('ShaderNodeMixRGB');mul.blend_type='MULTIPLY';mul.location=(220,330);mul.inputs[0].default_value=1
            l.new(mix.outputs[0],mul.inputs[1]);l.new(val.outputs[0],mul.inputs[2]);l.new(mul.outputs[0],p.inputs['Base Color'])
        elif channel=='Roughness':
            r=n.new('ShaderNodeMapRange');r.location=(220,20);r.inputs['To Min'].default_value=.80;r.inputs['To Max'].default_value=.96
            l.new(tex.outputs[0],r.inputs['Value']);l.new(r.outputs[0],p.inputs['Roughness'])
        else:
            normal=n.new('ShaderNodeNormalMap');normal.location=(220,-240);normal.uv_map='UV0';normal.inputs['Strength'].default_value=.12
            l.new(tex.outputs[0],normal.inputs['Color']);l.new(normal.outputs[0],p.inputs['Normal'])
    m['source']='CozySettlement/Mat/'+source_name+'; packed original BC/Roughness/Normal'
    m['mapping']='UV0: safe interior stone crops, face aspect preserved. No displacement. Not a lightmap.'
    m['crop_pixels_top_left']=json.dumps(PATCHES[kind])
    return m

def unwrap(o,kind):
    me=o.data;uv=me.uv_layers.get('UV0') or me.uv_layers.new(name='UV0')
    # Deterministic face selection, identical between house and courtyard sources.
    seed=int(hashlib.sha256(o.name.encode()).hexdigest()[:8],16)
    world=[o.matrix_world@v.co for v in me.vertices]
    nm=o.matrix_world.to_3x3().inverted().transposed()
    for poly in me.polygons:
        normal=nm@poly.normal;drop=max(range(3),key=lambda i:abs(normal[i]));axes=[i for i in range(3) if i!=drop]
        points=[world[me.loops[li].vertex_index] for li in poly.loop_indices]
        lo=[min(p[a] for p in points) for a in axes];hi=[max(p[a] for p in points) for a in axes]
        x0,y0,x1,y1=PATCHES[kind][(seed+poly.index)%len(PATCHES[kind])]
        width=(x1-x0)/1254;height=(y1-y0)/1254
        scale=.94*min(width/max(hi[0]-lo[0],1e-8),height/max(hi[1]-lo[1],1e-8))
        center=((x0+x1)/2508,1-(y0+y1)/2508)
        for li,p in zip(poly.loop_indices,points):
            uv.data[li].uv=(center[0]+(p[axes[0]]-(lo[0]+hi[0])/2)*scale,
                            center[1]+(p[axes[1]]-(lo[1]+hi[1])/2)*scale)
    o['material_stage']='Masonry v017; original geometry/pivot preserved'
    o['uv_method']='Aspect-preserving face projection into 3 safe source stone interiors; bevel inherits UV'

def verify():
    objects=targets();stats=inspect_geometry(objects);assert not stats['issues'],stats
    count=0
    for o in objects:
        kind='chimney' if o.name.startswith('SM_Chimney_') else 'field'
        expected='M_Cottage_'+('ChimneyStone' if kind=='chimney' else 'FieldStone')+'_A'
        assert o.data.materials[0].name==expected,o.name
        me=o.data;me.calc_loop_triangles();uv=me.uv_layers['UV0'].data
        for tri in me.loop_triangles:
            a,b,c=[uv[li].uv for li in tri.loops]
            area=abs((b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x))/2
            assert math.isfinite(area) and area>1e-12,(o.name,'UV area')
            count+=1
        for poly in me.polygons:
            coords=[uv[i].uv for i in poly.loop_indices]
            assert any(all(x0/1254-1e-6<=p.x<=x1/1254+1e-6 and 1-y1/1254-1e-6<=p.y<=1-y0/1254+1e-6 for p in coords)
                       for x0,y0,x1,y1 in PATCHES[kind]),(o.name,'UV outside safe crop')
    stats.update(base_uv_triangles_checked=count,uv_within_safe_crops=True,
                 foundation_and_steps=sum(not o.name.startswith('SM_Chimney_') for o in objects),
                 chimney_stones=sum(o.name.startswith('SM_Chimney_') for o in objects))
    return stats

def assign():
    materials={k:material(k) for k in ['field','chimney']}
    for o in targets():
        kind='chimney' if o.name.startswith('SM_Chimney_') else 'field'
        o.data=o.data.copy();o.data.materials.clear();o.data.materials.append(materials[kind])
        for p in o.data.polygons:p.material_index=0
        unwrap(o,kind)
    collar=bpy.data.objects['SM_Chimney_RoofCollar_A']
    collar.data=collar.data.copy();collar.data.materials.clear()
    collar.data.materials.append(bpy.data.materials['M_Cottage_RoofFlashing_A'])
    return verify()

def detail_views(sc,prefix=''):
    st=bpy.data.collections['90_STUDIO - not exported']
    cam=camera('QA_Masonry_Foundation',(-6,-8,2.8),(-.3,-2,.6),4.6,st)
    render(sc,cam,REND/(prefix+'Foundation_Detail.png'),900)
    cam=camera('QA_Masonry_Chimney',(-8,-5,8),(-2.94,.72,5.65),2.8,st)
    render(sc,cam,REND/(prefix+'Chimney_Detail.png'),900)

def build(mode):
    kind='house' if mode=='preview' else mode;target=source(kind,'v017')
    if mode!='preview':assert not target.exists(),target
    bpy.ops.wm.open_mainfile(filepath=str(source(kind,'v016')));bpy.context.view_layer.update()
    before=HELP['DIGEST'](list(bpy.data.objects));stats=assign()
    assert before==HELP['DIGEST'](list(bpy.data.objects))
    sc=bpy.context.scene;hero=sc.camera
    if mode=='preview':
        render(sc,hero,REND/'Preview.png',750);detail_views(sc,'Preview_');return
    target.parent.mkdir(parents=True,exist_ok=True);bpy.ops.wm.save_as_mainfile(filepath=str(target))
    stats.update(geometry_and_pivots_unchanged=True,file=str(target.relative_to(ROOT)))
    (ROOT/'QA'/('masonry_v017_'+mode+'.json')).write_text(json.dumps(stats,indent=2),encoding='utf-8')
    render(sc,hero,REND/('Courtyard_Hero.png' if mode=='assembly' else 'House_Hero.png'),1100)
    if mode=='house':detail_views(sc)
    print('MASONRY_COMPLETE',mode,flush=True)

def readback():
    reports=[]
    for mode in ['house','assembly']:
        bpy.ops.wm.open_mainfile(filepath=str(source(mode,'v016')));bpy.context.view_layer.update()
        before=HELP['DIGEST'](list(bpy.data.objects))
        bpy.ops.wm.open_mainfile(filepath=str(source(mode,'v017')));bpy.context.view_layer.update()
        assert before==HELP['DIGEST'](list(bpy.data.objects)),mode
        stats=verify();images=[]
        for name in ['M_Cottage_FieldStone_A','M_Cottage_ChimneyStone_A']:
            images += [n.image for n in bpy.data.materials[name].node_tree.nodes if n.type=='TEX_IMAGE']
        assert len(images)==6 and all(im.packed_file for im in images)
        contacts=HELP['audit']();maximum=max(r['max_gap'] for r in contacts);assert maximum<=.004
        assert bpy.context.scene.camera
        stats.update(mode=mode,geometry_and_pivots_unchanged=True,packed_masonry_images=6,ridge_max_gap_m=maximum,camera_saved=True)
        reports.append(stats)
    (ROOT/'QA/masonry_v017_readback.json').write_text(json.dumps(reports,indent=2),encoding='utf-8')
    print('MASONRY_READBACK_COMPLETE',flush=True)

def audit():
    rows=[]
    for name in ['02_FOUNDATION','06_CHIMNEY','09_DETAILS']:
        for o in bpy.data.collections[name].all_objects:
            if o.type=='MESH':
                rows.append({'collection':name,'name':o.name,'dims':list(o.dimensions),'verts':len(o.data.vertices),'materials':[m.name for m in o.data.materials if m]})
    (ROOT/'QA/masonry_v016_inventory.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
    print(json.dumps(rows),flush=True)

if __name__=='__main__':
    mode=sys.argv[sys.argv.index('--')+1]
    REND.mkdir(parents=True,exist_ok=True)
    if mode=='audit':
        bpy.ops.wm.open_mainfile(filepath=str(source('house','v016')));bpy.context.view_layer.update();audit()
    elif mode=='validate':readback()
    else:build(mode)
