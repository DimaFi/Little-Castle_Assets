from pathlib import Path
exec(Path(__file__).with_name('build_cottage_v2.py').read_text(encoding='utf-8').split('# Export and document')[0])
# Remove intersecting ornamental arch; build continuous lintel and modest keystone.
remove_prefix(['Door arch voussoir'])
cube('Entrance lintel',(.65,-2.20,2.48),(1.64,.30,.24),stones[3],.05)
cube('Entrance keystone',(.65,-2.23,2.52),(.27,.34,.33),stones[4],.035)
# Lower the original straight gable mesh where the curved roof sags.
for ob in assets:
    if ob.name.startswith('Plastered gables'):
        for v in ob.data.vertices:
            if v.co.z>4: v.co.z=roof_z(v.co.x,v.co.y)-.19
    if ob.name.startswith('Gable timber'):
        ob.hide_render=True
# Remove main roof tiles beneath the dormer; the underlay remains watertight.
for ob in list(assets):
    if ob.name.startswith('Hand laid terracotta') and .78<ob.location.x<2.08 and -.64<ob.location.y<.83:
        assets.remove(ob); bpy.data.objects.remove(ob,do_unlink=True)
# Matching roof flashing covers the dormer/roof joint rather than leaving floating cheeks.
for y in [-.53,.73]:
    beam('Dormer cheek flashing',(.84,y,roof_z(.84,y)+.035),(1.96,y,roof_z(1.96,y)+.035),.14,roofm[0])
beam('Dormer front flashing',(1.98,-.57,roof_z(1.98,-.57)+.05),(1.98,.77,roof_z(1.98,.77)+.05),.17,roofm[0])
# Extend dormer cheeks into the roof, making a closed exterior junction.
for y in [-.44,.64]: cube('Dormer lower cheek',(1.38,y,4.23),(.95,.10,.78),plaster,.025)
# Curved gable infill follows the actual roof rather than a straight triangle.
remove_prefix(['Plastered gables'])
for y in [-2.0,2.0]:
    vv=[]; ff=[]
    for i in range(25):
        x=-2.5+5*i/24; vv.extend([(x,y,3.27),(x,y,roof_z(x,y)-.10)])
    for i in range(24): ff.append((2*i,2*i+2,2*i+3,2*i+1))
    me=bpy.data.meshes.new('Curved gable'); me.from_pydata(vv,[],ff); me.update(); ob=bpy.data.objects.new('Curved gable infill',me); bpy.context.collection.objects.link(ob); ob.data.materials.append(plaster); assets.append(ob)
    ob.modifiers.new('Gable thickness','SOLIDIFY').thickness=.15
# Merge evaluated mesh into one game object; preserve the editable source separately.
for ob in list(assets):
    if ob.hide_render: assets.remove(ob); bpy.data.objects.remove(ob,do_unlink=True)
bpy.ops.object.select_all(action='DESELECT')
for ob in assets: ob.select_set(True)
bpy.context.view_layer.objects.active=assets[0]
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'Cottage_03_editable.blend'))
bpy.ops.object.convert(target='MESH'); bpy.ops.object.join(); house=bpy.context.object; house.name='SM_Cottage_03'
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.normals_make_consistent(inside=False); bpy.ops.uv.smart_project(island_margin=.015); bpy.ops.object.mode_set(mode='OBJECT')
bpy.context.scene.cursor.location=(0,0,0); bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
bpy.ops.export_scene.fbx(filepath=os.path.join(OUT,'Cottage_03.fbx'),use_selection=True,object_types={'MESH'},apply_unit_scale=True,axis_forward='-Y',axis_up='Z',bake_anim=False)
grass=mat('Preview sage',(.24,.30,.18)); cube('Preview ground',(0,0,-.14),(200,200,.2),grass,0)
world=bpy.context.scene.world; world.use_nodes=True; world.node_tree.nodes['Background'].inputs[1].default_value=.5
bpy.ops.object.light_add(type='AREA',location=(-3,-5,10)); bpy.context.object.data.energy=1900; bpy.context.object.data.size=6; bpy.context.object.rotation_euler=(Vector((0,0,2))-bpy.context.object.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(); cam=bpy.context.object; cam.data.type='ORTHO'; cam.data.ortho_scale=10.5
scene=bpy.context.scene; scene.camera=cam; scene.render.engine='CYCLES'; scene.cycles.samples=24; scene.cycles.use_denoising=True; scene.render.resolution_x=1000; scene.render.resolution_y=1000; scene.render.resolution_percentage=100
for label,pos in [('front',(10,-14,10)),('rear',(-10,14,9)),('roof',(9,-8,15))]:
    cam.location=pos; cam.rotation_euler=(Vector((0,0,2.6))-cam.location).to_track_quat('-Z','Y').to_euler(); scene.render.filepath=os.path.join(OUT,'Cottage_03_'+label+'.png'); bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'Cottage_03_preview.blend'))
