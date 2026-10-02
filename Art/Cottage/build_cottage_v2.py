"""Second art pass. Reuses v1 construction, but never overwrites v1 outputs."""
from pathlib import Path
exec(Path(__file__).with_name('build_cottage.py').read_text(encoding='utf-8').split('# Export only architecture')[0])
def remove_prefix(prefixes):
    for ob in list(assets):
        if any(ob.name.startswith(p) for p in prefixes):
            assets.remove(ob); bpy.data.objects.remove(ob,do_unlink=True)
remove_prefix(['Roof backing','Roof shingle','Ridge cap','Chimney','Foundation','Door lintel'])
stones=[mat('Limestone variation '+str(i),(.36+i*.025,.34+i*.024,.28+i*.020)) for i in range(6)]
glass=mat('Muted amber glass',(.30,.24,.12))
# A continuous shallow sag down the ridge, flared eaves and unequal slopes.
def roof_z(x,y):
    t=abs(x)/3.02
    return 5.15-.18*math.cos(y*.64)-1.9*t+.24*t*t+.045*math.sin(y*1.8+x)
def surface(name,x0,x1,y0,y1,nx,ny,material):
    vv=[]; ff=[]
    for i in range(nx+1):
        x=x0+(x1-x0)*i/nx
        for j in range(ny+1):
            y=y0+(y1-y0)*j/ny; vv.append((x,y,roof_z(x,y)-.09))
    for i in range(nx):
        for j in range(ny):
            k=i*(ny+1)+j; ff.append((k,k+ny+1,k+ny+2,k+1))
    me=bpy.data.meshes.new(name); me.from_pydata(vv,[],ff); me.update(); ob=bpy.data.objects.new(name,me); bpy.context.collection.objects.link(ob); ob.data.materials.append(material); assets.append(ob)
    so=ob.modifiers.new('Roof thickness','SOLIDIFY'); so.thickness=.11
for side in [-1,1]:
    surface('Curved roof underlay',0,side*3.07,-2.48,2.48,14,20,roofm[0])
    for row in range(9):
        x=side*(.16+row*.335)
        for col in range(13):
            y=-2.3+col*.378+(row%2)*.055
            z=roof_z(x,y)
            ob=cube('Hand laid terracotta',(x,y,z),(.46,.365+random.uniform(-.018,.018),.09),random.choice(roofm),.045)
            dx=(roof_z(x+.01,y)-roof_z(x-.01,y))/.02
            dy=(roof_z(x,y+.01)-roof_z(x,y-.01))/.02
            ob.rotation_euler=(math.atan(dy),-math.atan(dx),random.uniform(-.025,.025))
for i in range(14):
    y=-2.36+i*.365
    ob=cube('Curving ridge cap',(0,y,roof_z(0,y)+.085),(.32,.40,.19),random.choice(roofm),.085)
for side in [-1,1]:
    for y in [-2.47,2.48]:
        for i in range(10):
            a=side*i*.305; b=side*(i+1)*.305
            beam('Curved oak fascia',(a,y,roof_z(a,y)-.13),(b,y,roof_z(b,y)-.13),.15)
# Low hand-laid masonry, with bounded variation instead of uniform blocks.
cube('Foundation core',(0,0,.26),(5.07,4.07,.5),stone,.04)
for row in range(2):
    z=.14+row*.245
    for y in [-2.075,2.075]:
        for i in range(11):
            x=-2.32+i*.465
            ob=cube('Foundation front stone',(x+random.uniform(-.025,.025),y,z),(.445,.27,.23),random.choice(stones),.055); ob.rotation_euler[1]=random.uniform(-.04,.04)
    for x in [-2.56,2.56]:
        for i in range(9):
            ob=cube('Foundation side stone',(x,-1.88+i*.47,z),(.26,.45,.235),random.choice(stones),.055); ob.rotation_euler[0]=random.uniform(-.035,.035)
# Chimney in staggered masonry courses.
cube('Chimney core',(-1.45,.86,4.95),(.55,.59,2.0),stone,.04)
for row in range(8):
    z=4.10+row*.24
    for dx in [-.17,.17]:
        for dy in [-.18,.18]:
            cube('Chimney masonry',(-1.45+dx+random.uniform(-.015,.015),.86+dy,z),(.33,.35,.23),random.choice(stones),.035)
cube('Chimney cap',(-1.45,.86,6.0),(.83,.85,.17),stones[3],.06)
cube('Chimney opening',(-1.45,.86,6.09),(.43,.45,.025),dark,.02)
# Dormer faces the visible right-hand roof plane.
cube('Dormer plaster',(1.38,.1,4.58),(.95,1.18,.93),plaster,.06)
vv=[(.89,-.49,5.02),(1.90,-.49,5.02),(.89,.10,5.64),(1.90,.10,5.64),(.89,.69,5.02),(1.90,.69,5.02)]
me=bpy.data.meshes.new('Dormer gable'); me.from_pydata(vv,[],[(0,2,4),(1,5,3),(0,1,3,2),(2,3,5,4),(0,4,5,1)]); me.update(); ob=bpy.data.objects.new('Dormer gable',me); bpy.context.collection.objects.link(ob); ob.data.materials.append(plaster); assets.append(ob)
cube('Dormer window dark',(1.915,.1,4.73),(.055,.72,.78),dark,.045)
cube('Dormer amber glass',(1.95,.1,4.73),(.04,.61,.68),glass,.035)
for y in [-.29,.49]: cube('Dormer window frame',(1.98,y,4.73),(.12,.095,.89),wood,.025)
for z in [4.30,5.16]: cube('Dormer sill frame',(1.98,.1,z),(.20,.87,.10),wood,.025)
cube('Dormer mullion',(1.985,.1,4.73),(.09,.055,.76),wood,.015)
for side in [-1,1]:
    for row in range(4):
        y=.1+side*(.1+row*.19)
        for col in range(4):
            ob=cube('Dormer roof tile',(.89+col*.32,y,5.72-abs(y-.1)*.93),(.355,.32,.08),random.choice(roofm),.04); ob.rotation_euler[0]=-side*.75
    beam('Dormer rake',(2.02,.1,5.66),(2.02,.1+side*.82,4.90),.12)
# Expressive entrance, with a shallow arch above the original door.
for i in range(9):
    angle=math.pi*i/8
    ob=cube('Door arch voussoir',(.65+.70*math.cos(angle),-2.20,2.35+.30*math.sin(angle)),(.24,.26,.24),random.choice(stones),.035); ob.rotation_euler[1]=-(angle-math.pi/2)*.35
for side in [-1,1]:
    for i in range(5): cube('Door surround stone',(.65+side*.70,-2.17,.70+i*.32),(.24,.24,.30),random.choice(stones),.045)
# Lantern with thick enough silhouette to survive a distant camera.
beam('Lantern wall bracket',(1.63,-2.06,2.69),(1.63,-2.55,2.69),.055,iron)
glow=mat('Lantern warm glass',(.9,.48,.14)); bs=glow.node_tree.nodes.get('Principled BSDF'); bs.inputs['Emission Color'].default_value=(1,.40,.08,1); bs.inputs['Emission Strength'].default_value=.4
cube('Lantern glass',(1.63,-2.52,2.37),(.23,.23,.34),glow,.02)
for z in [2.17,2.57]: cube('Lantern metal cap',(1.63,-2.52,z),(.32,.32,.07),iron,.025)
for x in [1.50,1.76]:
    for y in [-2.65,-2.39]: beam('Lantern corner',(x,y,2.19),(x,y,2.56),.026,iron)
beam('Lantern hanger',(1.63,-2.52,2.58),(1.63,-2.52,2.69),.035,iron)
# Small natural irregularities in the visible timber and shutters.
for ob in assets:
    if ob.name.startswith(('Corner post','Open shutter','Window upright')): ob.rotation_euler[1]+=random.uniform(-.02,.02)
    if ob.name.startswith(('Front rear crossbeam','Base timber')): ob.rotation_euler[1]+=.012
# Export and document measured geometry rather than estimating it.
bpy.ops.object.select_all(action='DESELECT')
for ob in assets: ob.select_set(True)
bpy.context.view_layer.objects.active=assets[0]
bpy.ops.export_scene.fbx(filepath=os.path.join(OUT,'Cottage_02.fbx'),use_selection=True,object_types={'MESH'},apply_unit_scale=True,axis_forward='-Y',axis_up='Z',use_mesh_modifiers=True,add_leaf_bones=False,bake_anim=False)
dg=bpy.context.evaluated_depsgraph_get(); triangles=0
for ob in assets:
    ev=ob.evaluated_get(dg); m=ev.to_mesh(); m.calc_loop_triangles(); triangles+=len(m.loop_triangles); ev.to_mesh_clear()
print('ARCHITECTURE',len(assets),'objects;',triangles,'evaluated triangles')
grass=mat('Preview sage',(.24,.30,.18)); cube('Preview ground',(0,0,-.14),(200,200,.2),grass,0)
world=bpy.context.scene.world; world.use_nodes=True; world.node_tree.nodes['Background'].inputs[0].default_value=(.65,.76,.9,1); world.node_tree.nodes['Background'].inputs[1].default_value=.4
bpy.ops.object.light_add(type='AREA',location=(-3,-5,10)); bpy.context.object.data.energy=1900; bpy.context.object.data.shape='DISK'; bpy.context.object.data.size=6; bpy.context.object.rotation_euler=(Vector((0,0,2))-bpy.context.object.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(10,-14,10)); cam=bpy.context.object; cam.rotation_euler=(Vector((0,0,2.65))-cam.location).to_track_quat('-Z','Y').to_euler(); cam.data.type='ORTHO'; cam.data.ortho_scale=10.4
scene=bpy.context.scene; scene.camera=cam; scene.render.engine='CYCLES'; scene.cycles.samples=48; scene.cycles.use_denoising=True; scene.render.resolution_x=1200; scene.render.resolution_y=1100; scene.render.resolution_percentage=100; scene.view_settings.view_transform='AgX'; scene.render.image_settings.file_format='PNG'
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'Cottage_02.blend'))
scene.render.filepath=os.path.join(OUT,'Cottage_02_preview.png'); bpy.ops.render.render(write_still=True)
