"""v014: UV and packed existing RoofTile maps. Background Blender -- [house|assembly|validate|checker]."""
import sys,json,math,runpy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from kit_geometry import *
ROOT=Path(__file__).resolve().parents[1];MAT=ROOT.parents[1]/'Mat/RoofTile'
HELP=runpy.run_path(str(Path(__file__).with_name('19_roof_solids.py')),run_name='roof_helpers')
DIGEST=HELP['HELPER']['digest'];SCALE=.43
REND=ROOT/'Renders/Checkpoint_09/v014'
STUDY=ROOT/'Source/Materials/v014/Roof_Material_Study_v003.blend'
GROUPS=['ROOF_TILES_MAIN','ROOF_TILES_DORMER','ROOF_RIDGE_CAPS']
SUPPORT=['SM_Roof_Main_Front_A','SM_Roof_Main_Back_A','SM_Dormer_Hood_A']
FLASH=['SM_Dormer_ValleyFlashing_A','SM_Dormer_FrontApron_A']

def clay_objects():return [o for name in GROUPS for o in bpy.data.collections[name].objects]

def plain(name,color,rough,metal=0):
    m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*color,1)
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
    return m

def material():
    m=plain('M_Cottage_Terracotta_A',(.20,.065,.018),.8);n=m.node_tree.nodes;l=m.node_tree.links
    p=n.get('Principled BSDF');p.location=(900,50)
    uv=n.new('ShaderNodeUVMap');uv.uv_map='UV0';uv.location=(-1100,200)
    info=n.new('ShaderNodeObjectInfo');info.location=(-1100,-180)
    offset=n.new('ShaderNodeCombineXYZ');offset.location=(-680,50)
    for key,amount in [('X',.10),('Y',.16)]:
        mul=n.new('ShaderNodeMath');mul.operation='MULTIPLY';mul.inputs[1].default_value=amount
        l.new(info.outputs['Random'],mul.inputs[0]);l.new(mul.outputs[0],offset.inputs[key])
    add=n.new('ShaderNodeVectorMath');add.operation='ADD';add.location=(-460,200)
    l.new(uv.outputs[0],add.inputs[0]);l.new(offset.outputs[0],add.inputs[1])
    for i,channel in enumerate(['BaseColor','Roughness','Normal']):
        image=bpy.data.images.load(str(MAT/('RoofTile_'+channel+'.png')),check_existing=True)
        image.colorspace_settings.name='sRGB' if channel=='BaseColor' else 'Non-Color';image.pack()
        tex=n.new('ShaderNodeTexImage');tex.image=image;tex.extension='EXTEND';tex.location=(-220,350-i*320)
        l.new(add.outputs[0],tex.inputs['Vector'])
        if channel=='BaseColor':
            mix=n.new('ShaderNodeMixRGB');mix.inputs[0].default_value=.35;mix.inputs[2].default_value=(.26,.055,.012,1)
            mix.label='Soften photographic contrast';mix.location=(50,350);l.new(tex.outputs[0],mix.inputs[1])
            variation=n.new('ShaderNodeMapRange');variation.inputs['To Min'].default_value=.52;variation.inputs['To Max'].default_value=.78
            variation.location=(50,80);l.new(info.outputs['Random'],variation.inputs['Value'])
            multiply=n.new('ShaderNodeMixRGB');multiply.blend_type='MULTIPLY';multiply.inputs[0].default_value=1
            multiply.location=(500,280);l.new(mix.outputs[0],multiply.inputs[1]);l.new(variation.outputs[0],multiply.inputs[2])
            l.new(multiply.outputs[0],p.inputs['Base Color'])
        elif channel=='Roughness':
            r=n.new('ShaderNodeMapRange');r.inputs['To Min'].default_value=.65;r.inputs['To Max'].default_value=.90
            r.location=(350,-50);l.new(tex.outputs[0],r.inputs['Value']);l.new(r.outputs[0],p.inputs['Roughness'])
        else:
            normal=n.new('ShaderNodeNormalMap');normal.uv_map='UV0';normal.inputs['Strength'].default_value=.10
            normal.location=(350,-280);l.new(tex.outputs[0],normal.inputs['Color']);l.new(normal.outputs[0],p.inputs['Normal'])
    m['source']='CozySettlement/Mat/RoofTile; original packed maps'
    m['sampling']='Interior of tile image only, UV0 + per-object offset <= (0.10,0.16)'
    return m

def planar_uv(me,basis):
    coords=[Vector(tuple(v.co.dot(a) for a in basis)) for v in me.vertices]
    lo=[min(v[i] for v in coords) for i in range(3)]
    uv=me.uv_layers.get('UV0') or me.uv_layers.new(name='UV0')
    for p in me.polygons:
        normal=Vector(tuple(p.normal.dot(a) for a in basis));drop=max(range(3),key=lambda i:abs(normal[i]))
        axes=[i for i in range(3) if i!=drop]
        for li in p.loop_indices:
            co=coords[me.loops[li].vertex_index]
            uv.data[li].uv=(.30+(co[axes[0]]-lo[axes[0]])*SCALE,.25+(co[axes[1]]-lo[axes[1]])*SCALE)

def unwrap(me,kind):
    if kind=='ROOF_TILES_DORMER':
        # Each small curved tile gets a tangent frame; no projection through the full roof slope.
        normal=sum((p.normal*p.area for p in me.polygons if p.normal.z>.01),Vector()).normalized()
        y=Vector((0,1,0));x=y.cross(normal).normalized();z=x.cross(y).normalized()
        planar_uv(me,[x,y,z])
    elif kind=='ROOF_RIDGE_CAPS':
        planar_uv(me,[Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1))])
        uv=me.uv_layers['UV0'];minx=min(v.co.x for v in me.vertices)
        for p in me.polygons:
            radial=Vector((0,p.center.y,p.center.z)).normalized()
            if abs(p.normal.dot(radial))>.65:
                for li in p.loop_indices:
                    co=me.vertices[me.loops[li].vertex_index].co
                    angle=max(0,min(math.pi,math.atan2(co.z,co.y)))
                    uv.data[li].uv=(.30+.205*angle*SCALE,.25+(co.x-minx)*SCALE)
    else:planar_uv(me,[Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1))])

def assign():
    mat=material();done={}
    for group in GROUPS:
        for o in bpy.data.collections[group].objects:
            key=o.data.as_pointer()
            if key not in done:
                old=o.data;new=old.copy();new.materials.clear();new.materials.append(mat)
                for p in new.polygons:p.material_index=0
                unwrap(new,group);done[key]=new
                # Preserve sharing, including hidden reusable prototypes.
                for alias in list(bpy.data.objects):
                    if alias.type=='MESH' and alias.data==old:alias.data=new
                done[new.as_pointer()]=new
            o['uv_method']='Metric tile tangent projection' if group!='ROOF_RIDGE_CAPS' else 'Cylindrical arc with planar rims/end faces'
            o['uv_scale_per_local_m']=SCALE;o['stage']='ROOF MATERIALS v014; UV0; no lightmap/LOD'
    under=plain('M_Cottage_RoofUnderlay_A',(.14,.052,.021),.91)
    lead=plain('M_Cottage_RoofFlashing_A',(.085,.079,.069),.72,.5)
    for name in SUPPORT+FLASH:
        o=bpy.data.objects[name];o.data=o.data.copy();o.data.materials.clear();o.data.materials.append(under if name in SUPPORT else lead)
        for p in o.data.polygons:p.material_index=0

def verify_uv():
    count=0;bounds=[1.,1.,0.,0.]
    for me in {o.data for o in clay_objects()}:
        assert me.materials[0].name=='M_Cottage_Terracotta_A'
        me.calc_loop_triangles();uv=me.uv_layers['UV0'].data
        for t in me.loop_triangles:
            a,b,c=[uv[i].uv for i in t.loops];area=abs((b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x))/2
            assert math.isfinite(area) and area>1e-12,(me.name,'UV collapse',area)
            count+=1
        for v in uv:
            u,w=v.uv;assert .28<=u<=.66 and .20<=w<=.66,(me.name,u,w)
            bounds=[min(bounds[0],u),min(bounds[1],w),max(bounds[2],u),max(bounds[3],w)]
    return {'unique_mesh_uv_triangles':count,'uv_bounds':bounds,'sample_bounds_with_offset':[bounds[0],bounds[1],bounds[2]+.10,bounds[3]+.16]}

def source(mode,version):
    return ROOT/'Source'/('Assembly' if mode=='assembly' else 'Roof')/version/('Cottage_Courtyard.blend' if mode=='assembly' else 'House_Cottage_A.blend')

def study():
    assert not STUDY.exists(),STUDY
    examples=[next(o for o in bpy.data.collections['ROOF_TILES_MAIN'].objects if len(o.data.vertices)==40),
              next(iter(bpy.data.collections['ROOF_TILES_DORMER'].objects)),next(iter(bpy.data.collections['ROOF_RIDGE_CAPS'].objects))]
    sc=bpy.data.scenes.new('Roof_Material_Study');bpy.context.window.scene=sc
    sc.unit_settings.system='METRIC';sc.unit_settings.scale_length=1;sc.render.engine='CYCLES';sc.cycles.samples=32;sc.cycles.use_denoising=True
    sc.render.threads_mode='FIXED';sc.render.threads=8;sc.view_settings.view_transform='AgX'
    col=collection('Roof_Material_Samples')
    for i,o in enumerate(examples):
        n=o.copy();n.data=o.data.copy();col.objects.link(n);n.parent=None;n.rotation_euler=(0,0,0);n.scale=(1,1,1)
        # Lay each small piece on the studio plane, preserving its mesh for inspection.
        if i==1:
            normal=sum((p.normal*p.area for p in n.data.polygons if p.normal.z>.01),Vector()).normalized()
            n.rotation_mode='QUATERNION';n.rotation_quaternion=normal.rotation_difference(Vector((0,0,1)))
        rot=n.rotation_quaternion.to_matrix() if n.rotation_mode=='QUATERNION' else n.rotation_euler.to_matrix()
        vs=[rot@v.co for v in n.data.vertices]
        lo=Vector(tuple(min(v[a] for v in vs) for a in range(3)));hi=Vector(tuple(max(v[a] for v in vs) for a in range(3)))
        n.location=Vector(((i-1)*.72,0,.015))-Vector(((lo.x+hi.x)/2,(lo.y+hi.y)/2,lo.z))
    st=studio(sc,bpy.data.materials['M_Blockout_Grey']);cam=camera('CAM_Roof_Samples',(1.7,-3,2.7),(0,0,.15),2.6,st);sc.camera=cam
    for o in st.objects:
        if o.name.startswith('Studio ground'):o.location.z=-.125
    transfer=ROOT/'QA/roof_material_study_transfer.blend'
    STUDY.parent.mkdir(parents=True,exist_ok=True);bpy.data.libraries.write(str(transfer),{sc},fake_user=True)
    open_study_native(transfer)
    sc=bpy.context.scene;render(sc,sc.camera,REND/'Roof_Material_Samples.png',950)

def open_study_native(library):
    assert not STUDY.exists(),STUDY
    bpy.ops.wm.open_mainfile(filepath=str(library))
    bpy.context.window.scene=bpy.data.scenes['Roof_Material_Study']
    bpy.ops.wm.save_as_mainfile(filepath=str(STUDY))

def build(mode):
    target=source(mode,'v014');assert not target.exists(),target
    bpy.ops.wm.open_mainfile(filepath=str(source(mode,'v012')));bpy.context.view_layer.update();before=DIGEST(list(bpy.data.objects))
    assign();uv=verify_uv();assert DIGEST(list(bpy.data.objects))==before
    closure=HELP['validate_roof']();sc=bpy.context.scene
    target.parent.mkdir(parents=True,exist_ok=True);bpy.ops.wm.save_as_mainfile(filepath=str(target))
    report=dict(uv,objects=len(clay_objects()),geometry_and_pivots_unchanged=True,geometry=closure['geometry'],file=str(target.relative_to(ROOT)))
    (ROOT/'QA'/('roof_materials_v014_'+mode+'.json')).write_text(json.dumps(report,indent=2),encoding='utf-8')
    if mode=='house':
        render(sc,sc.camera,REND/'House_Hero.png',1000)
        st=bpy.data.collections['90_STUDIO - not exported']
        cam=camera('QA_Roof_Detail',(-8,-7,6.3),(-1.3,-.8,3.85),5,st);render(sc,cam,REND/'Roof_Detail.png',950)
        cam=camera('QA_Rear',(8,9,7),(0,0,3),9.5,st);render(sc,cam,REND/'House_Rear.png',900)
        study()
    else:render(sc,sc.camera,REND/'Courtyard_Hero.png',1100)
    print('ROOF_MATERIALS_COMPLETE',mode,flush=True)

def readback():
    report=[]
    for mode in ['house','assembly']:
        bpy.ops.wm.open_mainfile(filepath=str(source(mode,'v012')));bpy.context.view_layer.update();before=DIGEST(list(bpy.data.objects))
        bpy.ops.wm.open_mainfile(filepath=str(source(mode,'v014')));bpy.context.view_layer.update();assert DIGEST(list(bpy.data.objects))==before
        uv=verify_uv();HELP['validate_roof']()
        images=[n.image for n in bpy.data.materials['M_Cottage_Terracotta_A'].node_tree.nodes if n.type=='TEX_IMAGE']
        assert len(images)==3 and all(i.packed_file for i in images)
        report.append(dict(uv,name=mode,geometry_unchanged=True,roof_closed=True,packed_images=3))
    bpy.ops.wm.open_mainfile(filepath=str(STUDY));sc=bpy.context.scene
    assert sc.name=='Roof_Material_Study','Native file must open directly into the material study'
    objs=list(bpy.data.collections['Roof_Material_Samples'].objects);stats=inspect_geometry(objs)
    assert len(objs)==3 and not stats['issues'] and sc.camera
    report.append(dict(name='material_study',**stats))
    (ROOT/'QA/roof_materials_v014_readback.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('ROOF_MATERIALS_READBACK_COMPLETE',flush=True)

def checker():
    bpy.ops.wm.open_mainfile(filepath=str(source('house','v014')));sc=bpy.context.scene
    mat=plain('QA_Roof_UV_Checker',(.5,.5,.5),.8);n=mat.node_tree.nodes;l=mat.node_tree.links
    uv=n.new('ShaderNodeUVMap');uv.uv_map='UV0';ch=n.new('ShaderNodeTexChecker');ch.inputs['Scale'].default_value=20
    ch.inputs['Color1'].default_value=(.025,.09,.16,1);ch.inputs['Color2'].default_value=(.65,.8,.8,1)
    l.new(uv.outputs[0],ch.inputs['Vector']);l.new(ch.outputs[0],n.get('Principled BSDF').inputs['Base Color'])
    for me in {o.data for o in clay_objects()}:me.materials[0]=mat
    cam=camera('QA_UV',(-8,-7,6.3),(-1.3,-.8,3.85),5,bpy.data.collections['90_STUDIO - not exported'])
    render(sc,cam,REND/'Roof_UV_Check.png',950)

if __name__=='__main__':
    REND.mkdir(parents=True,exist_ok=True);mode=sys.argv[sys.argv.index('--')+1]
    if mode=='validate':readback()
    elif mode=='checker':checker()
    elif mode=='study':
        bpy.ops.wm.open_mainfile(filepath=str(source('house','v014')));study()
    elif mode=='native-study':open_study_native(ROOT/'Source/Materials/v014/Roof_Material_Study_v002.blend')
    else:build(mode)
