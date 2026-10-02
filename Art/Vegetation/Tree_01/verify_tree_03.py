import bpy,os,json
from mathutils import Vector
ROOT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'Tree_03')
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT,'Tree_03_Master.blend'))
# FBX only understands a limited subset of shader nodes. Supply direct image links.
m=bpy.data.materials['M_Tree03_Foliage_Atlas'];p=m.node_tree.nodes.get('Principled BSDF')
im=next(n for n in m.node_tree.nodes if n.type=='TEX_IMAGE')
m.node_tree.links.new(im.outputs['Color'],p.inputs['Base Color']);m.node_tree.links.new(im.outputs['Alpha'],p.inputs['Alpha'])
for level in range(3):
    bpy.ops.object.select_all(action='DESELECT')
    objs=[bpy.data.objects[f'Tree03_LOD{level}_{part}'] for part in ['Trunk','Canopy']]
    for ob in objs:ob.hide_viewport=False;ob.select_set(True)
    bpy.context.view_layer.objects.active=objs[0]
    bpy.ops.export_scene.fbx(filepath=os.path.join(ROOT,f'Tree_03_LOD{level}.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',bake_anim=False,path_mode='COPY',embed_textures=True)
report={}
for level in range(3):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=os.path.join(ROOT,f'Tree_03_LOD{level}.fbx'))
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
    assert len(meshes)==2,(level,len(meshes))
    report[str(level)]={}
    for ob in meshes:
        assert ob.data.uv_layers,ob.name
        ob.data.calc_loop_triangles()
        report[str(level)][ob.name]={'triangles':len(ob.data.loop_triangles),'uv_layers':len(ob.data.uv_layers),'materials':len(ob.data.materials)}
    foliage=next(o for o in meshes if 'Canopy' in o.name)
    textures=[n.image.name for m in foliage.data.materials for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image]
    assert any('Foliage' in n for n in textures),textures
    report[str(level)]['foliage_textures']=textures
with open(os.path.join(ROOT,'export_validation.json'),'w') as f:json.dump(report,f,indent=2)
print('EXPORT_VALIDATED',report,flush=True)
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT,'Tree_03_Master.blend'))
for o in bpy.data.objects:
    if '_LOD0_' in o.name:o.hide_render=True
    if '_LOD2_' in o.name:o.hide_viewport=False;o.hide_render=False
s=bpy.context.scene;s.render.engine='BLENDER_EEVEE_NEXT';s.render.resolution_x=900;s.render.resolution_y=900
s.render.filepath=os.path.join(ROOT,'Tree_03_LOD2_check.png');bpy.ops.render.render(write_still=True)
