"""Bake the approved Tree04 source material and export compact whole-cluster LODs."""
import bpy,os,json,shutil,math
from mathutils import Vector
ROOT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'Tree_04')
TEX=os.path.join(ROOT,'Textures');os.makedirs(TEX,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT,'Tree_04_Master.blend'))
scene=bpy.context.scene;wood=bpy.data.objects['Tree04_TrunkRoots_LOD0']
assert len(wood.data.polygons)>15000
def active(o):
    bpy.ops.object.select_all(action='DESELECT');o.hide_viewport=False;o.hide_set(False);o.select_set(True);bpy.context.view_layer.objects.active=o
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
for d in prefs.devices:d.use=d.type=='OPTIX'
scene.cycles.device='GPU';scene.cycles.samples=16;scene.render.engine='CYCLES'
original_visibility={o.name:o.hide_render for o in scene.objects}
for ob in scene.objects:ob.hide_render=ob!=wood
active(wood)
m=wood.data.materials[0];m.use_fake_user=True;n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF');out=n.get('Material Output')
uvnode=n.new('ShaderNodeUVMap');uvnode.uv_map='BarkFlow'
for node in list(n):
    if node.type=='TEX_IMAGE':l.new(uvnode.outputs['UV'],node.inputs['Vector'])
    if node.type=='NORMAL_MAP':node.uv_map='BarkFlow'
uv=wood.data.uv_layers.new(name='BakedUV');wood.data.uv_layers.active=uv;uv.active_render=True
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(72),island_margin=.008);bpy.ops.object.mode_set(mode='OBJECT')
scene.render.bake.margin=12;scene.render.bake.use_selected_to_active=False
target=n.new('ShaderNodeTexImage');emit=n.new('ShaderNodeEmission');images={}
surface=out.inputs['Surface'].links[0].from_socket
for label,kind,socket in [('BaseColor','EMIT','Base Color'),('Roughness','EMIT','Roughness'),('Normal','NORMAL',None),('AO','AO',None)]:
    im=bpy.data.images.new('T_Tree04_Bark_'+label,width=2048,height=2048,alpha=False)
    im.colorspace_settings.name='sRGB' if label=='BaseColor' else 'Non-Color';target.image=im
    for node in n:node.select=False
    target.select=True;n.active=target
    if socket:
        source=p.inputs[socket].links[0].from_socket;l.new(source,emit.inputs['Color']);l.new(emit.outputs[0],out.inputs['Surface'])
    else:l.new(surface,out.inputs['Surface'])
    bpy.ops.object.bake(type=kind)
    im.filepath_raw=os.path.join(TEX,'T_Tree04_Bark_'+label+'.png');im.file_format='PNG';im.save();im.pack();images[label]=im
    print('BAKED',label,flush=True)
l.new(surface,out.inputs['Surface']);n.remove(emit);n.remove(target)
bm=bpy.data.materials.new('M_Tree04_Bark_Baked');bm.use_nodes=True;bn=bm.node_tree.nodes;bl=bm.node_tree.links;bp=bn.get('Principled BSDF');bp.inputs['Specular IOR Level'].default_value=.24
for label,socket in [('BaseColor','Base Color'),('Roughness','Roughness'),('Normal',None)]:
    node=bn.new('ShaderNodeTexImage');node.image=images[label]
    if socket:bl.new(node.outputs['Color'],bp.inputs[socket])
    else:
        norm=bn.new('ShaderNodeNormalMap');bl.new(node.outputs['Color'],norm.inputs['Color']);bl.new(norm.outputs['Normal'],bp.inputs['Normal'])
wood.data.materials.clear();wood.data.materials.append(bm)
for ob in scene.objects:ob.hide_render=original_visibility[ob.name]
leaf=bpy.data.materials['M_Tree04_Leaf_Atlas']
leaf_im=next(node.image for node in leaf.node_tree.nodes if node.type=='TEX_IMAGE')
source=os.path.abspath(os.path.join(ROOT,'../../../../Mat/T_Foliage/T_Foliage_BaseColor.png'))
shutil.copy2(source,os.path.join(TEX,'T_Foliage_BaseColor.png'))

exports=bpy.data.collections.new('GAME_EXPORT_LODS');scene.collection.children.link(exports)
def put_export(ob):
    for c in list(ob.users_collection):c.objects.unlink(ob)
    exports.objects.link(ob)
def duplicate(ob,name,ratio=1):
    c=ob.copy();c.data=ob.data.copy();c.name=name;exports.objects.link(c);c.parent=None;c.matrix_world=ob.matrix_world.copy()
    if c.data.uv_layers.get('BakedUV'):
        for layer in list(c.data.uv_layers):
            if layer.name!='BakedUV':c.data.uv_layers.remove(layer)
        c.data.uv_layers.active_index=0;c.data.uv_layers[0].active_render=True
    active(c)
    if ratio<1:
        mod=c.modifiers.new('Game mesh reduction','DECIMATE');mod.ratio=ratio;bpy.ops.object.modifier_apply(modifier=mod.name)
    return c
def combine(objects,name,material,enlarge=1):
    verts=[];faces=[];uvs=[];colors=[]
    for ob in objects:
        me=ob.data;offset=len(verts);matrix=ob.matrix_world
        verts.extend(tuple(matrix@(v.co*enlarge)) for v in me.vertices)
        faces.extend(tuple(offset+i for i in p.vertices) for p in me.polygons)
        localuv=[(0,0)]*len(me.vertices)
        if me.uv_layers:
            layer=me.uv_layers.active
            for loop in me.loops:localuv[loop.vertex_index]=tuple(layer.data[loop.index].uv)
        uvs.extend(localuv)
        col=me.color_attributes.get('LeafTint')
        colors.extend(tuple(x.color) for x in col.data) if col else colors.extend([(1,1,1,1)]*len(me.vertices))
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();ob=bpy.data.objects.new(name,me);exports.objects.link(ob);me.materials.append(material)
    uv=me.uv_layers.new(name='UVMap');col=me.color_attributes.new(name='LeafTint',type='FLOAT_COLOR',domain='POINT')
    for item,value in zip(col.data,colors):item.color=value
    for poly in me.polygons:
        poly.use_smooth=True
        for li in poly.loop_indices:uv.data[li].uv=uvs[me.loops[li].vertex_index]
    # Wind mask is independent of the color tint and exported as UV2 (height, branch tip).
    wind=me.uv_layers.new(name='WindData')
    for loop in me.loops:wind.data[loop.index].uv=(max(0,min(1,(me.vertices[loop.vertex_index].co.z-2)/5)),1)
    me.uv_layers.active_index=0;me.uv_layers[0].active_render=True
    return ob
shoots=sorted([o for o in scene.objects if '_LeafShoot_' in o.name],key=lambda o:o.name)
twigs=sorted([o for o in scene.objects if '_TwigShoot_' in o.name],key=lambda o:o.name)
infill=bpy.data.objects['Tree04_Crown_VolumeInfill'];secondary=bpy.data.objects['Tree04_SecondaryBranches']
lods={};stats={}
for level,ratio,step in [(0,.58,1),(1,.26,2),(2,.095,99)]:
    trunk=duplicate(wood,f'Tree04_LOD{level}_Wood',ratio)
    fol=combine((shoots[::step] if level<2 else [])+[infill],f'Tree04_LOD{level}_Foliage',leaf)
    objects=[trunk,fol]
    if level<2:
        twig=combine(twigs[::step]+[secondary],f'Tree04_LOD{level}_Twigs',bpy.data.materials['M_Tree04_YoungTwigs'])
        active(twig);dec=twig.modifiers.new('Simplify thin stems','DECIMATE');dec.ratio=.4 if level==0 else .23;bpy.ops.object.modifier_apply(modifier=dec.name);objects.append(twig)
    lods[level]=objects;stats[str(level)]={}
    for ob in objects:
        ob.data.calc_loop_triangles();stats[str(level)][ob.name]=len(ob.data.loop_triangles);ob.hide_render=True;ob.hide_set(True)
    print('LOD_STATS',level,stats[str(level)],flush=True)

# Direct texture connections for FBX's limited material translator.
lp=leaf.node_tree.nodes.get('Principled BSDF');ln=leaf.node_tree.nodes;ll=leaf.node_tree.links
tex=next(n for n in ln if n.type=='TEX_IMAGE');color=lp.inputs['Base Color'].links[0].from_socket;alpha=lp.inputs['Alpha'].links[0].from_socket
ll.new(tex.outputs['Color'],lp.inputs['Base Color']);ll.new(tex.outputs['Alpha'],lp.inputs['Alpha'])
for level,objects in lods.items():
    bpy.ops.object.select_all(action='DESELECT')
    for ob in objects:ob.hide_set(False);ob.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
    bpy.ops.export_scene.fbx(filepath=os.path.join(ROOT,f'Tree_04_LOD{level}.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',bake_anim=False,path_mode='COPY',embed_textures=True)
    for ob in objects:ob.hide_set(True)
ll.new(color,lp.inputs['Base Color']);ll.new(alpha,lp.inputs['Alpha'])
attachments=[]
for name in ['Tree03_Birdhouse_01','Tree03_Lantern_01','Tree02_Lantern_Cord','Tree02_OldKnot_Rim','Tree02_OldKnot_Recess']:
    ob=bpy.data.objects[name];attachments.append({'name':name,'location':list(ob.location),'scale':list(ob.scale),'rotation_euler':list(ob.rotation_euler)})
    if name in ['Tree03_Birdhouse_01','Tree03_Lantern_01']:
        active(ob);loc=ob.location.copy();ob.location=(0,0,0)
        bpy.ops.export_scene.fbx(filepath=os.path.join(ROOT,name.replace('Tree03','Tree04')+'.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',bake_anim=False,path_mode='COPY',embed_textures=True)
        ob.location=loc
with open(os.path.join(ROOT,'game_manifest.json'),'w') as f:json.dump({'triangles':stats,'attachments_blender_coordinates':attachments,'source_leaf_instances':len(shoots),'leaf_prototype_meshes':len(set(o.data.name for o in shoots)),'bark_maps':list(images)},f,indent=2)
scene.cycles.samples=48;scene.render.resolution_x=1500;scene.render.resolution_y=1500
cam=scene.camera;cam.location=(8,-16,8);cam.rotation_euler=(Vector((-.15,0,3.05))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=9.6
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,'Tree_04_Master.blend'))
for label,pos,target,scale in [('hero',(8,-16,8),(-.15,0,3.05),9.6),('detail',(3,-10,4.2),(0,-.05,1.65),4.5),('game',(8,-16,11),(0,0,3),17)]:
    cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;scene.render.filepath=os.path.join(ROOT,'Tree_04_'+label+'.png');bpy.ops.render.render(write_still=True)
print('PACKAGE_COMPLETE',stats,flush=True)
