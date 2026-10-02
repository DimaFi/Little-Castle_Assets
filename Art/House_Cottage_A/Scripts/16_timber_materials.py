"""v010: structural timber UV/materials. Run in background Blender -- [house|assembly|validate]."""
import sys, json, math, hashlib
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from kit_geometry import *

ROOT=Path(__file__).resolve().parents[1]
REND=ROOT/'Renders/Checkpoint_07/v010'
MODULE=ROOT/'Source/Modules/Timber_v001/SM_Cottage_TimberFrame_A.blend'
SCALE=.43
PREFIXES=('SM_Roof_Eave_', 'SM_Roof_Verge_', 'SM_Roof_Ridge_A', 'SM_Dormer_Fascia_')

def targets():
    members=list(bpy.data.collections['04_TIMBER'].all_objects)
    members += [o for o in bpy.data.collections['05_ROOF'].all_objects if o.name.startswith(PREFIXES)]
    return sorted((o for o in members if o.type=='MESH'),key=lambda o:o.name)

def digest(objects):
    result={}
    for o in objects:
        data={'parent':o.parent.name if o.parent else None,'matrix':[list(row) for row in o.matrix_world]}
        if o.type=='MESH':
            data.update(vertices=[list(v.co) for v in o.data.vertices],faces=[list(p.vertices) for p in o.data.polygons])
        result[o.name]=hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest()
    return result

def make_material():
    m=bpy.data.materials['M_Cottage_FrameWood_A'].copy();m.name='M_Cottage_StructuralTimber_A'
    # Same source palette as windows; darker framing establishes the large structural lines.
    mix=next(n for n in m.node_tree.nodes if n.type=='MIX_RGB')
    mix.inputs[0].default_value=.42;mix.inputs[2].default_value=(.115,.058,.024,1)
    mix.label='Structural timber: softened source, darker warm base'
    m.diffuse_color=(.20,.105,.045,1)
    m['note']='Packed existing T_Timber maps; grain follows each member. No displacement.'
    return m

def unwrap(o):
    """Physical arc length along rings, physical perimeter across; planar orthogonal caps."""
    me=o.data;assert len(me.vertices)%4==0,o.name
    count=len(me.vertices)//4;assert count>=2,o.name
    # Confirm this is the expected swept quad topology, not an arbitrary multiple of four.
    assert len(me.polygons)==2+4*(count-1),(o.name,len(me.polygons),count)
    world=o.matrix_world
    rings=[[world@me.vertices[4*i+j].co for j in range(4)] for i in range(count)]
    centers=[sum(ring,Vector())/4 for ring in rings]
    lengths=[0.]
    for i in range(1,count): lengths.append(lengths[-1]+(centers[i]-centers[i-1]).length)
    perimeter=[0.]
    for j in range(4):perimeter.append(perimeter[-1]+(rings[0][(j+1)%4]-rings[0][j]).length)
    h=int(hashlib.sha256(o.name.encode()).hexdigest()[:8],16)
    off_u=.07+(h%7)*.11;off_v=.06+((h//7)%4)*.075
    uv=me.uv_layers.get('UV0') or me.uv_layers.new(name='UV0')
    for p in me.polygons:
        ring_ids={me.loops[li].vertex_index//4 for li in p.loop_indices}
        corners={me.loops[li].vertex_index%4 for li in p.loop_indices}
        if len(ring_ids)==1:
            ring=rings[next(iter(ring_ids))];origin=ring[0]
            a=(ring[1]-origin).normalized();b=(ring[3]-origin).normalized()
            for li in p.loop_indices:
                d=world@me.vertices[me.loops[li].vertex_index].co-origin
                uv.data[li].uv=(off_u+d.dot(a)*SCALE,off_v+d.dot(b)*SCALE)
        else:
            assert len(ring_ids)==2 and len(corners)==2,o.name
            seam=corners=={0,3}
            for li in p.loop_indices:
                idx=me.loops[li].vertex_index;corner=idx%4
                uv.data[li].uv=(off_u+lengths[idx//4]*SCALE,
                                off_v+perimeter[4 if seam and corner==0 else corner]*SCALE)
    o['stage']='TIMBER MATERIALS v010; UV0 repeatable; no LOD/lightmap'
    o['uv_method']='Metric arc-length sweep + perimeter; orthogonal planar caps'
    o['uv_scale_per_m']=SCALE;o['material_role']='structural_timber'
    return {'name':o.name,'length_m':round(lengths[-1],4),'rings':count}

def verify(objects):
    stats=inspect_geometry(objects);assert not stats['issues'],stats
    checked=0
    for o in objects:
        me=o.data;uv=me.uv_layers['UV0'].data;me.calc_loop_triangles()
        assert me.materials[0].name=='M_Cottage_StructuralTimber_A',o.name
        for t in me.loop_triangles:
            a,b,c=[uv[li].uv for li in t.loops]
            area=abs((b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x))/2
            assert math.isfinite(area) and area>1e-12,(o.name,area)
            checked+=1
    stats.update(uv_triangles_checked=checked,uv_degenerate_faces=0)
    return stats

def save(target):
    assert not target.exists(),target
    target.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(target))

def checker(objects,sc,cam):
    m=bpy.data.materials.new('QA_Timber_Checker');m.use_nodes=True
    n=m.node_tree.nodes;l=m.node_tree.links
    uv=n.new('ShaderNodeUVMap');uv.uv_map='UV0'
    ch=n.new('ShaderNodeTexChecker');ch.inputs['Scale'].default_value=20
    ch.inputs['Color1'].default_value=(.025,.09,.16,1);ch.inputs['Color2'].default_value=(.65,.8,.8,1)
    l.new(uv.outputs[0],ch.inputs['Vector']);l.new(ch.outputs[0],n.get('Principled BSDF').inputs['Base Color'])
    previous=[o.data.materials[0] for o in objects]
    for o in objects:o.data.materials[0]=m
    render(sc,cam,REND/'Timber_UV_Check.png',850)
    for o,mat in zip(objects,previous):o.data.materials[0]=mat

def package(objects):
    assert not MODULE.exists(),MODULE
    MODULE.parent.mkdir(parents=True,exist_ok=True)
    sc=bpy.data.scenes.new('SM_Cottage_TimberFrame_A');bpy.context.window.scene=sc
    sc.unit_settings.system='METRIC';sc.unit_settings.scale_length=1
    sc.render.engine='CYCLES';sc.cycles.samples=24;sc.cycles.use_denoising=True
    sc.render.threads_mode='FIXED';sc.render.threads=8;sc.view_settings.view_transform='AgX'
    col=collection('SM_Cottage_TimberFrame_A')
    for o in objects:
        obj=o.copy();col.objects.link(obj);obj.matrix_world=o.matrix_world.copy()
    st=studio(sc,bpy.data.materials['M_Blockout_Grey'])
    ground=next(o for o in st.objects if o.name.startswith('Studio ground'));ground.location.z=-.125
    cam=camera('CAM_TimberFrame',(-10,-13,9),(0,0,2.8),10,st);sc.camera=cam
    bpy.data.libraries.write(str(MODULE),{sc},fake_user=True)
    render(sc,cam,REND/'Timber_Frame_Module.png',850)

def build(mode):
    source=ROOT/('Source/Materials/v009/House_Cottage_A.blend' if mode=='house' else 'Source/Assembly/v009/Cottage_Courtyard.blend')
    target=ROOT/('Source/Materials/v010/House_Cottage_A.blend' if mode=='house' else 'Source/Assembly/v010/Cottage_Courtyard.blend')
    assert not target.exists(),target
    bpy.ops.wm.open_mainfile(filepath=str(source));sc=bpy.context.scene;bpy.context.view_layer.update()
    before=digest(list(bpy.data.objects));objects=targets();mat=make_material();records=[]
    for o in objects:
        o.data=o.data.copy();records.append(unwrap(o));o.data.materials.clear();o.data.materials.append(mat)
        for p in o.data.polygons:p.material_index=0
    stats=verify(objects);assert digest(list(bpy.data.objects))==before,'Shape or transform changed'
    assert all(n.image.packed_file for n in mat.node_tree.nodes if n.type=='TEX_IMAGE')
    # Save default hero pose before temporary checker materials or extra module scenes.
    if mode=='house':sc.camera=bpy.data.objects['CAM_01_Hero_Front_Left']
    save(target)
    if mode=='house':
        render(sc,sc.camera,REND/'House_Hero.png',1000)
        st=bpy.data.collections['90_STUDIO - not exported']
        cam=camera('QA_Timber_Detail',(-8,-7,6.3),(-1.3,-.8,3.25),5.8,st)
        render(sc,cam,REND/'Timber_Detail.png',900)
        checker(objects,sc,cam)
        rear=camera('QA_Rear',(8,9,7),(0,0,2.9),9.5,st)
        render(sc,rear,REND/'House_Rear.png',900)
        package(objects)
    else:render(sc,sc.camera,REND/'Courtyard_Hero.png',1100)
    stats.update(parts=records,file=str(target.relative_to(ROOT)),geometry_and_pivots_unchanged=True)
    (ROOT/'QA'/('timber_v010_'+mode+'.json')).write_text(json.dumps(stats,indent=2),encoding='utf-8')
    print('TIMBER_COMPLETE',mode,stats['objects'],flush=True)

def readback():
    report=[]
    for mode in ['house','assembly']:
        folder='Materials' if mode=='house' else 'Assembly';file='House_Cottage_A.blend' if mode=='house' else 'Cottage_Courtyard.blend'
        bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Source'/folder/'v009'/file));bpy.context.view_layer.update()
        before=digest(list(bpy.data.objects))
        bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Source'/folder/'v010'/file));bpy.context.view_layer.update()
        assert digest(list(bpy.data.objects))==before,mode
        stats=verify(targets());stats.update(name=mode,geometry_and_pivots_unchanged=True);report.append(stats)
    bpy.ops.wm.open_mainfile(filepath=str(MODULE));sc=bpy.data.scenes['SM_Cottage_TimberFrame_A'];bpy.context.window.scene=sc
    objs=list(bpy.data.collections['SM_Cottage_TimberFrame_A'].all_objects);stats=verify(objs)
    assert sc.camera and sc.unit_settings.scale_length==1
    mat=objs[0].data.materials[0];images=[n.image for n in mat.node_tree.nodes if n.type=='TEX_IMAGE']
    assert len(images)==3 and all(im.packed_file for im in images)
    stats.update(name='SM_Cottage_TimberFrame_A',camera_saved=True,packed_images=3);report.append(stats)
    (ROOT/'QA/timber_v010_readback.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('TIMBER_READBACK_COMPLETE',len(report),flush=True)

if __name__=='__main__':
    REND.mkdir(parents=True,exist_ok=True)
    mode=sys.argv[sys.argv.index('--')+1]
    if mode=='validate':readback()
    else:build(mode)
