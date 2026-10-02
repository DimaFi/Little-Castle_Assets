"""Shared construction helpers for movable grey cottage modules. Metres, front -Y."""
import bpy, math, json
from pathlib import Path
from mathutils import Vector, Matrix
from geometry import *

def cylinder(name,a,b,r,col,mat,vertices=14,r2=None):
    a,b=Vector(a),Vector(b);d=b-a;r2=r if r2 is None else r2
    vv=[(rr*math.cos(i*2*math.pi/vertices),rr*math.sin(i*2*math.pi/vertices),z)
        for z,rr in [(0,r),(d.length,r2)] for i in range(vertices)]
    ff=[tuple(range(vertices-1,-1,-1)),tuple(range(vertices,2*vertices))]
    ff += [(i,(i+1)%vertices,(i+1)%vertices+vertices,i+vertices) for i in range(vertices)]
    o=mesh(name,vv,ff,col,mat,min(.006,r*.18,d.length*.20));o.location=a
    o.rotation_euler=d.to_track_quat('Z','Y').to_euler();return o

def tube(name,points,r,col,mat,sides=8):
    points=[Vector(p) for p in points];vv=[];ff=[]
    for i,p in enumerate(points):
        d=(points[min(i+1,len(points)-1)]-points[max(i-1,0)]).normalized()
        guide=Vector((0,1,0)) if abs(d.y)<.9 else Vector((0,0,1))
        u=d.cross(guide).normalized();v=d.cross(u).normalized()
        vv.extend([p+r*(u*math.cos(j*2*math.pi/sides)+v*math.sin(j*2*math.pi/sides)) for j in range(sides)])
    for i in range(len(points)-1):
        for j in range(sides):ff.append((i*sides+j,i*sides+(j+1)%sides,(i+1)*sides+(j+1)%sides,(i+1)*sides+j))
    ff.extend([tuple(range(sides-1,-1,-1)),tuple(range(len(vv)-sides,len(vv)))])
    return mesh(name,vv,ff,col,mat)

def lathe(name,profile,col,mat,sides=24):
    """Closed cross section supplied in (radius,z), including the inside wall."""
    vv=[(r*math.cos(i*2*math.pi/sides),r*math.sin(i*2*math.pi/sides),z) for r,z in profile for i in range(sides)]
    ff=[]
    for j in range(len(profile)):
        k=(j+1)%len(profile)
        for i in range(sides):ff.append((j*sides+i,j*sides+(i+1)%sides,k*sides+(i+1)%sides,k*sides+i))
    return mesh(name,vv,ff,col,mat,.004)

def root_empty(name,col,location=(0,0,0)):
    o=bpy.data.objects.new(name,None);col.objects.link(o);o.location=location;o.empty_display_size=.12
    o['pivot']='Module origin at ground or mounting point';return o

def parent_world(objects,root):
    bpy.context.view_layer.update()
    for o in objects:
        world=o.matrix_world.copy();o.parent=root;o.matrix_world=world

def bounds(objects):
    bpy.context.view_layer.update();pts=[o.matrix_world@Vector(c) for o in objects if o.type=='MESH' for c in o.bound_box]
    return [min(v[i] for v in pts) for i in range(3)],[max(v[i] for v in pts) for i in range(3)]

def inspect_geometry(objects):
    deps=bpy.context.evaluated_depsgraph_get();issues=[];triangles=0
    for o in objects:
        if o.type!='MESH':continue
        ev=o.evaluated_get(deps);me=ev.to_mesh();me.calc_loop_triangles();triangles+=len(me.loop_triangles)
        if any(not all(math.isfinite(c) for c in v.co) for v in me.vertices):issues.append(o.name+': nonfinite')
        if any(t.area<1e-10 for t in me.loop_triangles):issues.append(o.name+': degenerate')
        ev.to_mesh_clear()
    return {'objects':sum(o.type=='MESH' for o in objects),'triangles':triangles,'issues':issues}
