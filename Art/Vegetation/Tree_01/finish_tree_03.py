"""Textured hero tree; existing source textures and prop files remain intact."""
import bpy, math, random, os, json
from mathutils import Vector
ROOT=os.path.dirname(os.path.abspath(__file__))
OUT=os.path.join(ROOT,'Tree_03'); os.makedirs(OUT,exist_ok=True)
MAT=os.path.abspath(os.path.join(ROOT,'../../../Mat'))
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT,'Tree_02_Master.blend'))
r=random.Random(641)
for ob in list(bpy.data.objects):
    if '_LOD1_' in ob.name or '_LOD2_' in ob.name:bpy.data.objects.remove(ob,do_unlink=True)
trunk=bpy.data.objects['Tree02_LOD0_Trunk']; old=bpy.data.objects['Tree02_LOD0_Canopy']
positions=[old.data.vertices[i].co.copy() for i in range(6,len(old.data.vertices),7)]
bpy.data.objects.remove(old,do_unlink=True)
trunk.name='Tree03_LOD0_Trunk'

def image_node(m,relative,linear=False):
    im=bpy.data.images.load(os.path.join(MAT,relative),check_existing=True)
    if linear:im.colorspace_settings.name='Non-Color'
    im.pack(); n=m.node_tree.nodes.new('ShaderNodeTexImage');n.image=im;return n
def material(name,color,rough=.8):
    m=bpy.data.materials.new(name);m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough
    return m,p

# Branch-aware cylindrical coordinates. Each polygon uses a consistent local axis.
paths=[[(0,0,0),(-.1,.02,1.2),(.18,.08,2.72),(-.48,.12,4.05),(-.78,.15,4.78)],[(.08,.03,1.55),(.92,.1,3),(1.3,.06,3.88),(.78,.18,5.72)],[(-.02,0,2.2),(-1.42,-.16,3.32),(-2.82,-.04,4.35)],[(.12,.1,2.46),(.15,.72,3.12),(-.52,1.92,4.55)],[(.54,.04,2.62),(1.32,-.28,3.2),(2.65,-.48,4.35)]]
segments=[]
for path in paths:
    distance=0
    for aa,bb in zip(path,path[1:]):
        a,b=Vector(aa),Vector(bb); axis=(b-a).normalized();length=(b-a).length
        u=axis.cross(Vector((0,1,0))).normalized(); v=axis.cross(u).normalized()
        segments.append((a,axis,length,u,v,distance));distance+=length
uv=trunk.data.uv_layers.active
for poly in trunk.data.polygons:
    c=poly.center
    seg=min(segments,key=lambda s:(c-(s[0]+s[1]*max(0,min(s[2],(c-s[0]).dot(s[1]))))).length_squared)
    a,axis,length,u,v,dist=seg;coords=[]
    for li in poly.loop_indices:
        co=trunk.data.vertices[trunk.data.loops[li].vertex_index].co-a
        coords.append((li,math.atan2(co.dot(v),co.dot(u))/math.tau,(co.dot(axis)+dist)*.30))
    cross=max(x[1] for x in coords)-min(x[1] for x in coords)>.5
    for li,x,y in coords:uv.data[li].uv=(x+1 if cross and x<0 else x,y)
bark,p=material('M_Tree03_Bark',(.3,.17,.075));n=bark.node_tree.nodes;l=bark.node_tree.links
bc=image_node(bark,'Bark/Bark_BaseColor.png');l.new(bc.outputs['Color'],p.inputs['Base Color'])
nt=image_node(bark,'Bark/Bark_Normal.png',True);nm=n.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.28;l.new(nt.outputs['Color'],nm.inputs['Color']);l.new(nm.outputs['Normal'],p.inputs['Normal'])
p.inputs['Roughness'].default_value=.86
trunk.data.materials.clear();trunk.data.materials.append(bark)
for poly in trunk.data.polygons:poly.material_index=0

# Low-amplitude real relief complements the painted bark without needle-like microdetail.
distex=bpy.data.textures.new('Bark broad relief',type='IMAGE');distex.image=bpy.data.images.load(os.path.join(MAT,'Bark/Bark_Displacement.png'),check_existing=True)
disp=trunk.modifiers.new('Shallow bark sculpt','DISPLACE');disp.texture=distex;disp.texture_coords='UV';disp.strength=.032;disp.mid_level=.5
bpy.context.view_layer.objects.active=trunk;bpy.ops.object.modifier_apply(modifier=disp.name)

# A single atlas material and bent leaf surfaces; individual leaves are removed whole for LOD.
leaf,p=material('M_Tree03_Foliage_Atlas',(.3,.4,.1));n=leaf.node_tree.nodes;l=leaf.node_tree.links
bc=image_node(leaf,'T_Foliage/T_Foliage_BaseColor.png')
col=n.new('ShaderNodeVertexColor');col.layer_name='LeafTint'
mul=n.new('ShaderNodeMixRGB');mul.blend_type='MULTIPLY';mul.inputs[0].default_value=1;l.new(bc.outputs['Color'],mul.inputs[1]);l.new(col.outputs['Color'],mul.inputs[2]);l.new(mul.outputs[0],p.inputs['Base Color'])
alpha=n.new('ShaderNodeMath');alpha.operation='GREATER_THAN';alpha.inputs[1].default_value=.52;l.new(bc.outputs['Alpha'],alpha.inputs[0]);l.new(alpha.outputs[0],p.inputs['Alpha'])
p.inputs['Roughness'].default_value=.82;p.inputs['Specular IOR Level'].default_value=.15;p.inputs['Subsurface Weight'].default_value=.035
leaf.surface_render_method='DITHERED';leaf.use_transparency_overlap=False
# Bottom-row individual leaf bounds in the supplied atlas, top-origin pixels.
rects=[(12,960,214,1217),(218,970,424,1217),(422,1008,621,1217),(766,969,910,1215),(908,983,1068,1217),(1068,981,1243,1217)]
records=[]
for i in range(7800):
    center=positions[i%len(positions)].copy()
    if i>=len(positions):center+=Vector((r.uniform(-.18,.18),r.uniform(-.18,.18),r.uniform(-.12,.12)))
    normal=Vector((r.uniform(-.85,.85),r.uniform(-.85,.85),r.uniform(.25,1))).normalized()
    u=normal.cross(Vector((0,1,0))).normalized();v=normal.cross(u).normalized();angle=r.uniform(0,math.tau)
    u,v=u*math.cos(angle)+v*math.sin(angle),-u*math.sin(angle)+v*math.cos(angle)
    size=r.uniform(.25,.43);idx=r.randrange(len(rects));shade=r.uniform(.72,1.12)
    records.append((center,u,v,normal,size,idx,(shade*.94,shade,shade*.88,1)))
def canopy_mesh(level,stride,size_mult):
    vv=[];ff=[];uvs=[];colors=[]
    for center,u,v,normal,size,idx,tint in records[::stride]:
        x0,y0,x1,y1=rects[idx]; width=size*(x1-x0)/(y1-y0);base=len(vv)
        for row in range(3):
            for column in range(3):
                x=column/2;y=row/2
                vv.append(tuple(center+u*((x-.5)*width*size_mult)+v*((y-.5)*size*size_mult)+normal*(math.sin(x*math.pi)*math.sin(y*math.pi)*.012)))
                uvs.append(((x0+x*(x1-x0))/1254,1-(y1-y*(y1-y0))/1254));colors.append(tint)
        for row in range(2):
            for colu in range(2):
                k=base+row*3+colu;ff.append((k,k+1,k+4,k+3))
    me=bpy.data.meshes.new('LeafSurfaces');me.from_pydata(vv,[],ff);me.update()
    o=bpy.data.objects.new(f'Tree03_LOD{level}_Canopy',me);bpy.context.collection.objects.link(o);me.materials.append(leaf)
    uv=me.uv_layers.new(name='AtlasUV');c=me.color_attributes.new(name='LeafTint',type='FLOAT_COLOR',domain='POINT')
    for vtx,item,tint in zip(me.vertices,c.data,colors):item.color=tint
    for face in me.polygons:
        face.use_smooth=True
        for li in face.loop_indices:uv.data[li].uv=uvs[me.loops[li].vertex_index]
    return o
canopy=canopy_mesh(0,1,1)

# Restore original prop slots (the previous draft collapsed all birdhouse slots to wood).
for name in ['Tree02_Attachment_Birdhouse','Tree02_Attachment_Lantern','Tree02_Birdhouse_Mount']:
    if name in bpy.data.objects:bpy.data.objects.remove(bpy.data.objects[name],do_unlink=True)
props_dir=os.path.abspath(os.path.join(ROOT,'../../Props'))
props=[]
for file,name,loc,scale in [('Birdhouse_01','SM_Birdhouse_01',(.67,-.42,2.13),1.2),('Lantern_01','SM_Lantern_01',(-2.02,-.18,2.86),1.15)]:
    with bpy.data.libraries.load(os.path.join(props_dir,file+'.blend'),link=False) as (src,dst):dst.objects=[name]
    ob=dst.objects[0];bpy.context.collection.objects.link(ob);ob.name='Tree03_'+file;ob.location=loc;ob.scale=(scale,)*3;props.append(ob)
    for slot in ob.material_slots:
        if not slot.material:continue
        m=slot.material.copy();slot.material=m
        if 'oak' in m.name.lower():
            nn=m.node_tree.nodes;ll=m.node_tree.links;pp=nn.get('Principled BSDF')
            im=image_node(m,'DoorWood/DoorWood_A_BaseColor.png');im.projection='BOX';im.projection_blend=.25
            tc=nn.new('ShaderNodeTexCoord');ll.new(tc.outputs['Generated'],im.inputs['Vector']);ll.new(im.outputs['Color'],pp.inputs['Base Color'])
        if 'glass' in m.name.lower():
            pp=m.node_tree.nodes.get('Principled BSDF');pp.inputs['Emission Strength'].default_value=1.25
cord=bpy.data.objects['Tree02_Lantern_Cord'];a=Vector((-2.02,-.18,2.86));b=Vector((-2.02,-.18,3.66));cord.location=(a+b)*.5;cord.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();cord.dimensions=(.025,.025,(b-a).length)
for name in ['Tree02_OldKnot_Rim','Tree02_OldKnot_Recess']:
    ob=bpy.data.objects[name];ob.scale*=1.15
    if 'Rim' in name:ob.data.materials.clear();ob.data.materials.append(bark)

# Consistent LOD hierarchy, retaining whole leaves instead of shredding their silhouettes.
lods={0:[trunk,canopy]}
for level,ratio,stride,enlarge in [(1,.5,2,1.2),(2,.20,4,1.5)]:
    o=trunk.copy();o.data=trunk.data.copy();bpy.context.collection.objects.link(o);o.name=f'Tree03_LOD{level}_Trunk'
    mod=o.modifiers.new('Wood simplification','DECIMATE');mod.ratio=ratio;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name)
    c=canopy_mesh(level,stride,enlarge);lods[level]=[o,c]
    for ob in [o,c]:ob.hide_render=True

scene=bpy.context.scene
for o in bpy.data.objects:
    if o.type=='LIGHT' and o.data.type=='POINT':o.data.energy=2
    if o.type=='LIGHT' and o.data.type=='AREA':
        o.data.color=(1,.91,.77) if o.location.y<0 else (.84,.90,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.35
scene.view_settings.look='AgX - Medium High Contrast'
scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True
scene.render.resolution_x=1500;scene.render.resolution_y=1500
scene.camera.location=(8,-16,8);scene.camera.rotation_euler=(Vector((-.15,0,3.05))-scene.camera.location).to_track_quat('-Z','Y').to_euler();scene.camera.data.ortho_scale=9.6

report={}
# Temporarily expose direct image links for FBX's limited material translator.
leaf_p=leaf.node_tree.nodes.get('Principled BSDF')
leaf_im=next(n for n in leaf.node_tree.nodes if n.type=='TEX_IMAGE')
saved_color=leaf_p.inputs['Base Color'].links[0].from_socket
saved_alpha=leaf_p.inputs['Alpha'].links[0].from_socket
leaf.node_tree.links.new(leaf_im.outputs['Color'],leaf_p.inputs['Base Color'])
leaf.node_tree.links.new(leaf_im.outputs['Alpha'],leaf_p.inputs['Alpha'])
for level,objects in lods.items():
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:o.hide_viewport=False;o.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUT,f'Tree_03_LOD{level}.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',bake_anim=False,path_mode='COPY',embed_textures=True)
    report[f'LOD{level}']={}
    for o in objects:
        o.data.calc_loop_triangles();report[f'LOD{level}'][o.name]=len(o.data.loop_triangles)
        if level:o.hide_viewport=True
leaf.node_tree.links.new(saved_color,leaf_p.inputs['Base Color'])
leaf.node_tree.links.new(saved_alpha,leaf_p.inputs['Alpha'])
for prop in props:
    bpy.ops.object.select_all(action='DESELECT');prop.select_set(True);bpy.context.view_layer.objects.active=prop
    loc=prop.location.copy();prop.location=(0,0,0)
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUT,prop.name+'.fbx'),use_selection=True,axis_forward='-Z',axis_up='Y',bake_anim=False,path_mode='COPY',embed_textures=True)
    prop.location=loc
for im in bpy.data.images:
    if im.source=='FILE' and not im.packed_file:
        try:im.pack()
        except Exception:pass
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'Tree_03_Master.blend'))
with open(os.path.join(OUT,'mesh_statistics.json'),'w') as f:json.dump(report,f,indent=2)
for label,pos,target,scale in [('hero',(8,-16,8),(-.15,0,3.05),9.6),('detail',(3,-10,4.2),(0,-.05,1.9),4.7),('reverse',(-9,13,7),(0,0,3),9.7)]:
    cam=scene.camera;cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
    scene.render.filepath=os.path.join(OUT,'Tree_03_'+label+'.png');bpy.ops.render.render(write_still=True)
print('FINISHED',report,flush=True)
