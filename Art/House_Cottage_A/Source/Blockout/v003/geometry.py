"""Small deterministic modelling helpers. Blender metres, +Z up, front -Y."""
import bpy, bmesh, math
from mathutils import Vector

def collection(name, parent=None):
    c = bpy.data.collections.new(name)
    (parent or bpy.context.scene.collection).children.link(c)
    return c

def active(o):
    bpy.ops.object.select_all(action='DESELECT')
    o.select_set(True)
    bpy.context.view_layer.objects.active = o

def mesh(name, vertices, faces, col, material, bevel=0):
    me = bpy.data.meshes.new(name)
    me.from_pydata(vertices, [], faces)
    me.update()
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); col.objects.link(o)
    me.materials.append(material)
    o['stage'] = 'BLOCKOUT - no UV or final materials'
    if bevel:
        mod = o.modifiers.new('Soft large edges', 'BEVEL')
        mod.width = bevel; mod.segments = 3
        mod = o.modifiers.new('Weighted corner normals', 'WEIGHTED_NORMAL')
        mod.keep_sharp = True; mod.weight = 30
    return o

def box(name, center, size, col, material, bevel=.025):
    x,y,z = [s/2 for s in size]
    vv = [(-x,-y,-z),(-x,-y,z),(-x,y,-z),(-x,y,z),(x,-y,-z),(x,-y,z),(x,y,-z),(x,y,z)]
    ff = [(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)]
    o = mesh(name, vv, ff, col, material, bevel); o.location = center
    return o

def origin(o, point):
    bpy.context.view_layer.update()
    delta = o.matrix_world.inverted() @ Vector(point)
    for v in o.data.vertices: v.co -= delta
    o.location = point
    o['pivot'] = 'custom functional pivot, metres'
    return o

def beam(name, points, width, depth, col, material):
    """Continuous swept rectangular beam. Points, not noise, control the bow."""
    points = [Vector(p) for p in points]; verts=[]
    for i,p in enumerate(points):
        tangent=(points[min(i+1,len(points)-1)]-points[max(i-1,0)]).normalized()
        guide = Vector((0,1,0)) if abs(tangent.y)<.9 else Vector((1,0,0))
        a=tangent.cross(guide).normalized()*width/2
        b=tangent.cross(a).normalized()*depth/2
        verts.extend([p-a-b,p+a-b,p+a+b,p-a+b])
    faces=[(3,2,1,0)]
    for i in range(len(points)-1):
        for j in range(4): faces.append((i*4+j,i*4+(j+1)%4,(i+1)*4+(j+1)%4,(i+1)*4+j))
    faces.append(tuple(range(len(verts)-4,len(verts))))
    o=mesh(name,verts,faces,col,material,min(width,depth)*.14)
    return origin(o,points[0])

def bowed_beam(name,a,b,width,col,material,bow=.018):
    a,b=Vector(a),Vector(b)
    offset=Vector((0,0,bow)) if abs((b-a).normalized().z)<.9 else Vector((bow,0,0))
    points=[a.lerp(b,i/4)+offset*math.sin(math.pi*i/4) for i in range(5)]
    return beam(name,points,width,width,col,material)

def prism(name, outline, yfront, yback, col, material, bevel=.02):
    """Extrude an X/Z outline into Y."""
    n=len(outline)
    vv=[(x,y,z) for y in [yfront,yback] for x,z in outline]
    ff=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]
    ff += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    return mesh(name,vv,ff,col,material,bevel)

def arch_outline(cx, bottom, width, height, segments=18):
    r=width/2; spring=bottom+height-r
    return [(cx-r,bottom),(cx+r,bottom)]+[(cx+r*math.cos(math.pi*i/segments),spring+r*math.sin(math.pi*i/segments)) for i in range(segments+1)]

def cut(o, cutter):
    active(o)
    m=o.modifiers.new('Opening', 'BOOLEAN'); m.operation='DIFFERENCE'; m.solver='EXACT'; m.object=cutter
    # Cut before bevel to keep the opening crisp and bevel its new boundary.
    bpy.ops.object.modifier_move_up(modifier=m.name)
    if len(o.modifiers)>2: bpy.ops.object.modifier_move_up(modifier=m.name)
    bpy.ops.object.modifier_apply(modifier=m.name)
    bpy.data.objects.remove(cutter,do_unlink=True)

def grey_material():
    m=bpy.data.materials.new('M_Blockout_Grey'); m.diffuse_color=(.48,.48,.48,1); m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF'); p.inputs['Base Color'].default_value=(.48,.48,.48,1)
    p.inputs['Roughness'].default_value=.82
    return m

def setup():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s=bpy.context.scene; s.unit_settings.system='METRIC'; s.unit_settings.scale_length=1
    s.render.engine='CYCLES'; s.cycles.samples=24; s.cycles.use_denoising=True
    s.render.threads_mode='FIXED'; s.render.threads=8
    s.view_settings.view_transform='AgX'
    return s,grey_material()

def studio(scene, material):
    col=collection('90_STUDIO - not exported')
    box('Studio ground',(0,0,-.18),(200,200,.25),col,material,0)
    world=bpy.data.worlds.new('Neutral studio'); scene.world=world; world.use_nodes=True
    world.node_tree.nodes['Background'].inputs[0].default_value=(.32,.32,.32,1)
    world.node_tree.nodes['Background'].inputs[1].default_value=.55
    for name,pos,energy,size in [('Key',(-6,-8,12),2200,7),('Fill',(6,-1,8),1000,6),('Rim',(0,7,10),1800,5)]:
        d=bpy.data.lights.new(name,'AREA'); d.energy=energy; d.shape='DISK'; d.size=size
        o=bpy.data.objects.new(name,d); col.objects.link(o); o.location=pos
        o.rotation_euler=(Vector((0,0,2.7))-o.location).to_track_quat('-Z','Y').to_euler()
    return col

def camera(name, position, target, scale, col):
    d=bpy.data.cameras.new(name); d.type='ORTHO'; d.ortho_scale=scale; d.lens=50
    o=bpy.data.objects.new(name,d); col.objects.link(o); o.location=position
    o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
    return o

def render(scene, cam, path, resolution=960):
    scene.camera=cam; scene.render.resolution_x=resolution; scene.render.resolution_y=resolution
    scene.render.resolution_percentage=100; scene.render.filepath=str(path)
    bpy.ops.render.render(write_still=True)
