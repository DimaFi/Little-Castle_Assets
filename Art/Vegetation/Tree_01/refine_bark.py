import bpy, os, math
from mathutils import Vector
OUT=os.path.dirname(os.path.abspath(__file__))
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT,'Tree_01.blend'))
trunk=bpy.data.objects['SM_Tree01_Wood']
m=bpy.data.materials.new('Bark sculpted furrows'); m.use_nodes=True
n=m.node_tree.nodes; l=m.node_tree.links; p=n.get('Principled BSDF'); p.inputs['Roughness'].default_value=.91
tex=n.new('ShaderNodeTexCoord'); scale=n.new('ShaderNodeVectorMath'); scale.operation='MULTIPLY'; scale.inputs[1].default_value=(9,9,1.4); l.new(tex.outputs['Object'],scale.inputs[0])
noise=n.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value=2.2; noise.inputs['Detail'].default_value=3; noise.inputs['Roughness'].default_value=.72; l.new(scale.outputs[0],noise.inputs['Vector'])
ramp=n.new('ShaderNodeValToRGB'); ramp.color_ramp.elements[0].position=.26; ramp.color_ramp.elements[0].color=(.055,.028,.012,1); ramp.color_ramp.elements[1].position=.73; ramp.color_ramp.elements[1].color=(.34,.21,.105,1); l.new(noise.outputs['Fac'],ramp.inputs[0]); l.new(ramp.outputs[0],p.inputs['Base Color'])
bump=n.new('ShaderNodeBump'); bump.inputs['Strength'].default_value=.65; bump.inputs['Distance'].default_value=.085; l.new(noise.outputs['Fac'],bump.inputs['Height']); l.new(bump.outputs[0],p.inputs['Normal'])
trunk.data.materials.clear(); trunk.data.materials.append(m)
for face in trunk.data.polygons: face.material_index=0
mod=trunk.modifiers.new('Soft trunk contours','SUBSURF'); mod.levels=1; mod.render_levels=1
# Bake bark to portable maps so the detail is not limited to Blender shaders.
bpy.ops.object.select_all(action='DESELECT'); trunk.select_set(True); bpy.context.view_layer.objects.active=trunk
scene=bpy.context.scene; scene.render.engine='CYCLES'; scene.cycles.samples=8
for label,kind in [('BaseColor','DIFFUSE'),('Normal','NORMAL')]:
    img=bpy.data.images.new('Tree01_Bark_'+label,width=1024,height=1024,alpha=False)
    if label=='Normal': img.colorspace_settings.name='Non-Color'
    target=n.new('ShaderNodeTexImage'); target.image=img; n.active=target
    scene.render.bake.use_pass_direct=False; scene.render.bake.use_pass_indirect=False; scene.render.bake.use_pass_color=True; scene.render.bake.margin=8
    bpy.ops.object.bake(type=kind)
    img.filepath_raw=os.path.join(OUT,'Tree01_Bark_'+label+'.png'); img.file_format='PNG'; img.save(); img.pack()
scene.cycles.samples=32
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'Tree_01_bark_v2.blend'))
cam=scene.camera
for label,loc,target,scale in [('bark_close',(3,-5,3.1),(0,0,1.9),4.6),('bark_full',(10,-14,9),(0,0,3),10.6)]:
    cam.location=loc; cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler(); cam.data.ortho_scale=scale; scene.render.filepath=os.path.join(OUT,'Tree_01_'+label+'.png'); bpy.ops.render.render(write_still=True)
