import unreal
unreal.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
task=unreal.AssetImportTask()
task.filename='E:/Games_Develop/CozySettlement/Art/Cottage/Cottage_03.fbx'
task.destination_path='/Game/Art/Cottage'
task.automated=True; task.save=True; task.replace_existing=True
options=unreal.FbxImportUI(); options.import_mesh=True; options.import_materials=True; options.import_textures=False; options.import_as_skeletal=False
options.static_mesh_import_data.combine_meshes=True
options.static_mesh_import_data.auto_generate_collision=True
task.options=options
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
mesh=next((unreal.load_asset(p) for p in task.imported_object_paths if isinstance(unreal.load_asset(p),unreal.StaticMesh)),None)
if not mesh: raise RuntimeError('No cottage static mesh imported')
unreal.EditorLevelLibrary.new_level('/Game/Maps/CottageTest')
def actor(cls,label,loc):
    a=unreal.EditorLevelLibrary.spawn_actor_from_class(cls,unreal.Vector(*loc)); a.set_actor_label(label); return a
for i,(x,y) in enumerate([(0,0),(1100,0),(0,1100)]):
    a=actor(unreal.StaticMeshActor,'Cottage test '+str(i),(x,y,0)); a.static_mesh_component.set_static_mesh(mesh)
ground=actor(unreal.StaticMeshActor,'Flat test ground',(0,0,-25)); ground.static_mesh_component.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cube.Cube')); ground.set_actor_scale3d(unreal.Vector(60,60,.5))
sun=actor(unreal.DirectionalLight,'Afternoon sun',(0,0,1000)); sun.set_actor_rotation(unreal.Rotator(-40,-35,0),False)
actor(unreal.SkyLight,'Sky fill',(0,0,500)); actor(unreal.SkyAtmosphere,'Atmosphere',(0,0,0))
cam=actor(unreal.CameraActor,'Overview camera',(-1500,-1800,1500)); cam.set_actor_rotation(unreal.Rotator(-30,45,0),False)
unreal.EditorLevelLibrary.set_level_viewport_camera_info(unreal.Vector(-1500,-1800,1500),unreal.Rotator(-30,45,0))
unreal.EditorLevelLibrary.save_current_level(); unreal.EditorAssetLibrary.save_directory('/Game',only_if_is_dirty=False,recursive=True)
unreal.log('COTTAGE_SCENE_READY')
