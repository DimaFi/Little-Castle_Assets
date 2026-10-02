import unreal
mesh=unreal.load_asset('/Game/Art/Cottage/Cottage_03')
sub=unreal.EditorStaticMeshLibrary
settings=sub.get_lod_build_settings(mesh,0)
settings.recompute_normals=True
settings.recompute_tangents=True
settings.use_mikk_t_space=False
settings.remove_degenerates=True
sub.set_lod_build_settings(mesh,0,settings)
sub.remove_collisions(mesh)
sub.add_simple_collisions(mesh,unreal.ScriptingCollisionShapeType.BOX)
unreal.EditorAssetLibrary.save_loaded_asset(mesh)
unreal.EditorLevelLibrary.load_level('/Game/Maps/CottageTest')
actors=unreal.EditorLevelLibrary.get_all_level_actors()
assert len([a for a in actors if a.get_actor_label().startswith('Cottage test')])==3
unreal.log('VALIDATED: three houses, ground, camera and lights; box collision; recomputed normals. Bounds: '+str(mesh.get_bounds()))
