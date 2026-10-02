import bpy,os,json,math
from mathutils import Vector
ROOT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'Tree_04')
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT,'Tree_04_Master.blend'))
scene=bpy.context.scene
def select(objects):
    bpy.ops.object.select_all(action='DESELECT')
    for ob in objects:ob.hide_set(False);ob.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
leaf=bpy.data.materials['M_Tree04_Leaf_Atlas'];p=leaf.node_tree.nodes.get('Principled BSDF');l=leaf.node_tree.links
color=p.inputs['Base Color'].links[0].from_socket;alpha=p.inputs['Alpha'].links[0].from_socket;tex=next(n for n in leaf.node_tree.nodes if n.type=='TEX_IMAGE')
l.new(tex.outputs['Color'],p.inputs['Base Color']);l.new(tex.outputs['Alpha'],p.inputs['Alpha'])
levels={}
for level in range(3):
    obs=[o for o in scene.objects if o.name.startswith(f'Tree04_LOD{level}_')]
    for ob in obs:
        uv=ob.data.uv_layers
        if uv.get('BakedUV'):
            for layer in list(uv):
                if layer.name!='BakedUV':uv.remove(layer)
        uv.active_index=0;uv[0].active_render=True
        assert len(ob.data.polygons)>0
    select(obs);levels[level]=obs
    bpy.ops.export_scene.fbx(filepath=os.path.join(ROOT,f'Tree_04_LOD{level}.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',bake_anim=False,path_mode='COPY',embed_textures=True)
    for ob in obs:ob.hide_set(True)
attachments=[bpy.data.objects[n] for n in ['Tree03_Birdhouse_01','Tree03_Lantern_01','Tree02_Lantern_Cord','Tree02_OldKnot_Rim','Tree02_OldKnot_Recess']]
select(levels[0]+attachments)
bpy.ops.export_scene.fbx(filepath=os.path.join(ROOT,'Tree_04_Assembled_LOD0.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',bake_anim=False,path_mode='COPY',embed_textures=True)
for ob in levels[0]:ob.hide_set(True)
l.new(color,p.inputs['Base Color']);l.new(alpha,p.inputs['Alpha'])
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,'Tree_04_Master.blend'))
# Render actual exported geometry at game distance, including the far LOD.
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
for d in prefs.devices:d.use=d.type=='OPTIX'
scene.cycles.device='GPU';scene.cycles.samples=32;scene.render.resolution_x=1200;scene.render.resolution_y=1200
source=[o for o in scene.objects if '_LeafShoot_' in o.name or '_TwigShoot_' in o.name or o.name in ['Tree04_TrunkRoots_LOD0','Tree04_Crown_VolumeInfill','Tree04_SecondaryBranches']]
for o in source:o.hide_render=True
cam=scene.camera;cam.location=(8,-16,11);cam.rotation_euler=(Vector((0,0,3))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=17
for level in [0,2]:
    for o in levels[level]:o.hide_render=False;o.hide_set(False)
    scene.render.filepath=os.path.join(ROOT,f'Tree_04_LOD{level}_game_check.png');bpy.ops.render.render(write_still=True)
    for o in levels[level]:o.hide_render=True
report={}
for level in range(3):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=os.path.join(ROOT,f'Tree_04_LOD{level}.fbx'))
    objects=[o for o in bpy.context.scene.objects if o.type=='MESH'];assert len(objects)==(2 if level==2 else 3)
    report[str(level)]={}
    for o in objects:
        assert len(o.data.uv_layers)>0;o.data.calc_loop_triangles()
        assert all(math.isfinite(x) for v in o.data.vertices for x in v.co)
        if 'Wood' in o.name:assert o.data.uv_layers[0].name=='BakedUV'
        report[str(level)][o.name]={'triangles':len(o.data.loop_triangles),'materials':len(o.data.materials),'uv0':o.data.uv_layers[0].name}
with open(os.path.join(ROOT,'export_validation.json'),'w') as f:json.dump(report,f,indent=2)
print('VALIDATION_PASSED',report,flush=True)
