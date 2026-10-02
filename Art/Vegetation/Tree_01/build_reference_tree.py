from pathlib import Path
source=Path(__file__).with_name('build_tree.py').read_text(encoding='utf-8')
exec(source.split('branch([(0,0,0)')[0])
TEX='E:/Games_Develop/CozySettlement/Mat/Realistic_Bark_Texture_01_2k'
# Hand-directed silhouette: low massive fork, curving right leader, broad left limb.
def curved(points,radii):
    pts=[Vector(p) for p in points]; pp=[]; rr=[]
    for i in range(len(pts)-1):
        a=pts[max(0,i-1)]; b=pts[i]; c=pts[i+1]; d=pts[min(len(pts)-1,i+2)]
        for j in range(5):
            t=j/5; pp.append(.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t)); rr.append(radii[i]*(1-t)+radii[i+1]*t)
    pp.append(pts[-1]); rr.append(radii[-1]); branch(pp,rr,16)
curved([(0,0,-.12),(.1,0,.35),(.02,0,1.0),(.25,.02,1.8),(.32,.03,2.45),(.06,0,3.0),(-.5,.05,3.55),(-1.4,.05,4.1),(-2.35,.02,4.6)],[.70,.57,.48,.46,.40,.33,.27,.18,.025])
curved([(.21,.06,1.8),(.63,.08,2.7),(1.18,.10,3.45),(1.3,.1,4.1),(.9,.15,5.15),(.7,.2,6.0)],[.36,.32,.27,.19,.10,.012])
curved([(.15,.02,2.6),(-.55,-.18,3.0),(-1.5,-.40,3.35),(-2.5,-.35,3.6),(-3.05,-.2,4.0)],[.28,.25,.19,.10,.015])
curved([(.3,.12,2.5),(.2,.8,3.25),(.0,1.55,4),(-.5,2,4.8)],[.26,.21,.13,.02])
curved([(.7,.06,3.0),(1.5,-.3,3.6),(2.2,-.5,4.15),(2.8,-.6,4.5)],[.22,.17,.10,.015])
for i in range(6):
    a=i*math.tau/6; curved([(math.cos(a)*1.1,math.sin(a)*.95,-.04),(math.cos(a)*.60,math.sin(a)*.53,.12),(.08,0,.62)],[.03,.17,.27])
clusters=[]
# Overlapping lobes give one continuous dome, instead of pom-poms on long stems.
for z,rad,count,sz in [(4.25,2.25,12,1.02),(5.05,2.25,14,1.06),(5.85,1.50,10,1.04),(6.32,.65,5,.95)]:
    for i in range(count):
        a=i*math.tau/count+z; p=Vector((math.cos(a)*rad-.35,math.sin(a)*rad*.78,z+r.uniform(-.2,.2)))
        clusters.append((p,sz*1.08,sz,sz*.9))
for i in range(8): clusters.append((Vector((r.uniform(-1.3,1),r.uniform(-1,1),r.uniform(4.5,5.9))),1.0,1.0,1.0))
exec(source[source.index('def mesh_obj'):source.index('# Colors are stable')].replace('range(185)','range(230)').replace('r.uniform(.09,.16)','r.uniform(.075,.135)'))
# Fuse wood intersections into a single smooth surface.
bpy.ops.object.select_all(action='DESELECT'); trunk.select_set(True); bpy.context.view_layer.objects.active=trunk
rem=trunk.modifiers.new('Joined natural branch junctions','REMESH'); rem.mode='VOXEL'; rem.voxel_size=.047; bpy.ops.object.modifier_apply(modifier=rem.name)
sm=trunk.modifiers.new('Smooth junctions','SMOOTH'); sm.factor=.7; sm.iterations=4; bpy.ops.object.modifier_apply(modifier=sm.name)
for p in trunk.data.polygons:p.use_smooth=True
# Cylindrical UV around the tree with seam-aware triangles, vertical bark direction.
uv=trunk.data.uv_layers.new(name='BarkUV')
for poly in trunk.data.polygons:
    vals=[]
    for li in poly.loop_indices:
        co=trunk.data.vertices[trunk.data.loops[li].vertex_index].co; vals.append((li,math.atan2(co.y,co.x)/(2*math.pi),co.z*.38))
    crossing=max(v[1] for v in vals)-min(v[1] for v in vals)>.5
    for li,u,v in vals: uv.data[li].uv=((u+1 if crossing and u<0 else u)*2,v)
m=material('User bark PBR',(.25,.15,.08)); n=m.node_tree.nodes; l=m.node_tree.links; p=n.get('Principled BSDF')
for name,socket,noncolor in [('Albedo.jpg','Base Color',False),('Roughness.jpg','Roughness',True),('Normal.jpg',None,True)]:
    im=bpy.data.images.load(os.path.join(TEX,name),check_existing=True); im.colorspace_settings.name='Non-Color' if noncolor else 'sRGB'; im.pack(); node=n.new('ShaderNodeTexImage'); node.image=im
    if socket:l.new(node.outputs['Color'],p.inputs[socket])
    else:
        norm=n.new('ShaderNodeNormalMap'); norm.inputs['Strength'].default_value=.65; l.new(node.outputs['Color'],norm.inputs['Color']); l.new(norm.outputs['Normal'],p.inputs['Normal'])
trunk.data.materials.clear(); trunk.data.materials.append(m)
for poly in trunk.data.polygons:poly.material_index=0
oak=material('Birdhouse honey wood',(.40,.235,.095)); roof=material('Birdhouse blue slate',(.12,.20,.21)); black=material('Hole interior',(.012,.009,.005)); moss=material('Moss green',(.15,.22,.04))
props=[]
def box(name,loc,size,mat,bevel=.025):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc); o=bpy.context.object;o.name=name;o.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(mat);b=o.modifiers.new('Handmade soft edges','BEVEL');b.width=bevel;b.segments=3;props.append(o);return o
# Birdhouse beside the right side of the trunk, visible in the hero view.
box('Birdhouse mounting plank',(.86,-.38,2.42),(.15,.15,.95),oak)
body=box('Birdhouse body',(1.00,-.52,2.35),(.43,.39,.55),oak)
for side in [-1,1]:
    o=box('Birdhouse pitched roof',(1.0+side*.145,-.52,2.70),(.38,.53,.065),roof);o.rotation_euler[1]=side*.66
bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=.073,depth=.015,location=(1,-.722,2.43),rotation=(math.pi/2,0,0));o=bpy.context.object;o.name='Birdhouse entrance';o.data.materials.append(black);props.append(o)
box('Birdhouse perch',(1,-.81,2.26),(.045,.22,.04),oak,.012)
# Hollow knot visible on the front of the trunk.
bpy.ops.mesh.primitive_torus_add(major_radius=.14,minor_radius=.045,major_segments=32,minor_segments=8,location=(.21,-.445,1.37),rotation=(math.pi/2,0,0));o=bpy.context.object;o.name='Old knot rim';o.scale=(.8,1,1.3);o.data.materials.append(oak);props.append(o)
bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=12,radius=1,location=(.21,-.446,1.37));o=bpy.context.object;o.name='Knot dark recess';o.scale=(.105,.018,.165);o.data.materials.append(black);props.append(o)
rim=bpy.data.objects['Old knot rim']; rim.data.materials.clear();rim.data.materials.append(material('Knot weathered wood',(.13,.078,.032)))
metal=material('Lantern aged bronze',(.10,.105,.065)); amber=material('Lantern amber panes',(.52,.32,.08))
box('Lantern suspension',(-1.85,-.44,3.02),(.035,.035,.74),metal,.008)
box('Lantern panes',(-1.85,-.44,2.54),(.19,.19,.29),amber,.015)
for z in [2.37,2.71]:box('Lantern frame cap',(-1.85,-.44,z),(.27,.27,.05),metal,.015)
for x in [-1.96,-1.74]:
    for y in [-.55,-.33]:box('Lantern corner',(x,y,2.54),(.027,.027,.32),metal,.005)
assets=[trunk,canopy]+props
bpy.ops.object.select_all(action='DESELECT')
for o in assets:o.select_set(True)
bpy.context.view_layer.objects.active=trunk
bpy.ops.export_scene.fbx(filepath=os.path.join(OUT,'Tree_Reference_02.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Y',axis_up='Z',mesh_smooth_type='FACE',bake_anim=False,path_mode='COPY',embed_textures=True)
scene=bpy.context.scene
scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.65,.77,.9,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.35
ground=material('Preview moss ground',(.26,.30,.16));bpy.ops.mesh.primitive_plane_add(size=200);bpy.context.object.name='Preview ground';bpy.context.object.data.materials.append(ground)
for pos,energy,size in [((-4,-6,11),2400,5),((4,3,9),1300,4)]:
    bpy.ops.object.light_add(type='AREA',location=pos);o=bpy.context.object;o.data.energy=energy;o.data.size=size;o.rotation_euler=(Vector((0,0,3))-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add();cam=bpy.context.object;scene.camera=cam;cam.data.type='ORTHO'
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True;scene.render.resolution_x=1200;scene.render.resolution_y=1200;scene.render.resolution_percentage=100
for label,pos,target,scale in [('hero',(7,-16,8),(-.3,0,3.2),10),('detail',(3,-9,4),(0,0,1.9),4.5),('rear',(-9,12,8),(0,0,3.2),10)]:
    cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
    if label=='hero':bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'Tree_Reference_02.blend'))
    scene.render.filepath=os.path.join(OUT,'Tree_Reference_02_'+label+'.png');bpy.ops.render.render(write_still=True)
print('REFERENCE_TREE_DONE')
