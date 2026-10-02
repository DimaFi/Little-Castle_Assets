import bpy, os
from mathutils import Vector
OUT=os.path.dirname(os.path.abspath(__file__))
TEX='E:/Games_Develop/CozySettlement/Mat/Bark'
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT,'Tree_Reference_02.blend'))
trunk=bpy.data.objects['SM_Tree01_Wood']
material=bpy.data.materials.new('Bark_Stylized_User');material.use_nodes=True
nodes=material.node_tree.nodes;links=material.node_tree.links;p=nodes.get('Principled BSDF')
p.inputs['Specular IOR Level'].default_value=.25
uv=nodes.new('ShaderNodeTexCoord');mapping=nodes.new('ShaderNodeVectorMath');mapping.operation='MULTIPLY';mapping.inputs[1].default_value=(.70,.85,1);links.new(uv.outputs['UV'],mapping.inputs[0])
def texture(filename,color=False):
    image=bpy.data.images.load(os.path.join(TEX,filename),check_existing=True);image.colorspace_settings.name='sRGB' if color else 'Non-Color';image.pack()
    n=nodes.new('ShaderNodeTexImage');n.image=image;links.new(mapping.outputs[0],n.inputs['Vector']);return n
base=texture('Bark_BaseColor.png',True);links.new(base.outputs['Color'],p.inputs['Base Color'])
rough=texture('Bark_Roughness.png');links.new(rough.outputs['Color'],p.inputs['Roughness'])
normaltex=texture('Bark_Normal.png');normal=nodes.new('ShaderNodeNormalMap');normal.inputs['Strength'].default_value=.45;links.new(normaltex.outputs['Color'],normal.inputs['Color']);links.new(normal.outputs[0],p.inputs['Normal'])
# AO is supplied separately for Unreal; avoid multiplying shadows baked in the painted base.
ao=texture('Bark_AO.png');ao.label='AO available for Unreal; not multiplied into painted color'
trunk.data.materials.clear();trunk.data.materials.append(material)
for face in trunk.data.polygons:face.material_index=0
scene=bpy.context.scene;cam=scene.camera;scene.cycles.samples=24
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'Tree_Reference_03_Bark.blend'))
bpy.ops.object.select_all(action='DESELECT')
for obj in scene.objects:
    if obj.type=='MESH' and obj.name!='Preview ground':obj.select_set(True)
bpy.context.view_layer.objects.active=trunk
bpy.ops.export_scene.fbx(filepath=os.path.join(OUT,'Tree_Reference_03_Bark.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Y',axis_up='Z',mesh_smooth_type='FACE',bake_anim=False,path_mode='COPY',embed_textures=True)
for label,pos,target,scale in [('detail',(3,-9,4),(0,0,1.9),4.5),('hero',(7,-16,8),(-.3,0,3.2),10)]:
    cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;scene.render.filepath=os.path.join(OUT,'Tree_Reference_03_'+label+'.png');bpy.ops.render.render(write_still=True)
print('STYLIZED_BARK_READY')
