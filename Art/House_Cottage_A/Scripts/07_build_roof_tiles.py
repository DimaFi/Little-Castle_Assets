"""Bounded roof pass. Shared main tiles/caps, unique cuts only near roof junctions.
Reads refinement v005, writes NEW revision. No textures or engine export.
"""
from pathlib import Path
import sys,argparse,math,json,shutil
sys.path.insert(0,str(Path(__file__).parent))
from geometry import *
from mathutils import Matrix
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--revision',required=True)
args=p.parse_args(sys.argv[sys.argv.index('--')+1:]);assert args.revision.isalnum()
out=ROOT/'Source/Roof'/args.revision
if out.exists():raise FileExistsError(out)
out.mkdir(parents=True);rend=ROOT/'Renders/Checkpoint_03'/args.revision;rend.mkdir(parents=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Source/Refinement/v005/House_Cottage_A.blend'))
s=bpy.context.scene;mat=bpy.data.materials['M_Blockout_Grey'];R=bpy.data.collections['05_ROOF']
main=collection('ROOF_TILES_MAIN',R);dormer=collection('ROOF_TILES_DORMER',R);ridge=collection('ROOF_RIDGE_CAPS',R)
lib=bpy.data.collections['80_MODULE_LIBRARY - hidden prototypes']

def rz(x,y):
    t=abs(y)/2.94
    return 5.64-.22*(1-(x/3.57)**2)-3.05*t+.62*t*t+(.035 if y>0 else 0)*t+.025*(x/3.57)*t
def bake(o):
    # Hidden prototype collections may return an unevaluated mesh through the depsgraph.
    # Temporarily link into a visible collection and explicitly apply the modifiers.
    temp=bpy.data.collections.new('TEMP_Roof_Modifier_Apply')
    bpy.context.scene.collection.children.link(temp);temp.objects.link(o)
    hidden=o.hide_get();viewport=o.hide_viewport
    try:
        o.hide_viewport=False;o.hide_set(False);bpy.context.view_layer.update();active(o)
        for modifier in list(o.modifiers):bpy.ops.object.modifier_apply(modifier=modifier.name)
    finally:
        o.hide_viewport=viewport;o.hide_set(hidden)
        temp.objects.unlink(o);bpy.data.collections.remove(temp)
def solid(name,verts,faces,col,thick=.035):
    o=mesh(name,verts,faces,col,mat)
    m=o.modifiers.new('Clay thickness','SOLIDIFY');m.thickness=thick;m.offset=-1
    m=o.modifiers.new('Soft lip','BEVEL');m.width=.006;m.segments=1
    bake(o);return o

cache={}
def template(width,length):
    key=(round(width,4),round(length,4))
    if key in cache:return cache[key]
    vv=[];ff=[]
    for j in range(4):
        t=j/3
        for i in range(5):
            u=i/4;x=(u-.5)*(width-(.018 if j==0 else 0))
            vv.append((x,length*t,.016*math.sin(math.pi*u)+.020*(1-t)))
    for j in range(3):
        for i in range(4):
            k=j*5+i;ff.append((k,k+1,k+6,k+5))
    o=solid('SM_RoofTile_Shared_'+str(len(cache)),vv,ff,lib)
    o['pivot']='Centre lower lip, +Y uphill';cache[key]=o;return o

def cutter(name,xy):
    n=len(xy);vv=[(x,y,z) for z in [2.7,7] for x,y in xy]
    ff=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    o=mesh(name,vv,ff,R,mat);o.hide_render=True;return o
hood=bpy.data.objects['SM_Dormer_Hood_A'];profile=[(v.co.x,v.co.z) for v in list(hood.data.vertices)[:33]]
joint=[(v.co.x,v.co.y) for v in list(hood.data.vertices)[-33:]]
maskxy=[(-.23,-2.43),(1.27,-2.43)]+[(.52+(x-.52)*1.065,y+.045) for x,y in reversed(joint)]
chimxy=[(-3.43,.20),(-2.45,.20),(-2.45,1.24),(-3.43,1.24)]
masks=[(maskxy,cutter('TEMP_DormerMask',maskxy)),(chimxy,cutter('TEMP_ChimneyMask',chimxy))]
def inside(x,y,poly):
    hit=False
    for (a,b),(c,d) in zip(poly,poly[1:]+poly[:1]):
        if (b>y)!=(d>y) and x<(c-a)*(y-b)/(d-b)+a:hit=not hit
    return hit

cut_count=0
for side in [-1,1]:
    for row in range(11):
        ay=2.98-row*.28;y=side*ay
        dy=(rz(0,y+.001)-rz(0,y-.001))/.002
        length=min(.52,ay*math.sqrt(1+dy*dy)+.065)
        bounds=[-3.61];q=-3.61+(.164 if row%2 else .328)
        while q<3.60:bounds.append(q);q+=.328
        bounds.append(3.61)
        for col,(a,b) in enumerate(zip(bounds,bounds[1:])):
            if b-a<.06:continue
            x=(a+b)/2;proto=template(b-a-.008,length)
            o=proto.copy();o.data=proto.data;main.objects.link(o);o.name=f'SM_Tile_{side}_{row:02}_{col:02}'
            dx=(rz(x+.001,y)-rz(x-.001,y))/.002;dy=(rz(x,y+.001)-rz(x,y-.001))/.002
            normal=Vector((-dx,-dy,1)).normalized();up=Vector((0,-side,-side*dy)).normalized();across=up.cross(normal).normalized()
            o.rotation_euler=Matrix((across,up,normal)).transposed().to_euler()
            # Deterministic 0..3 mm height variation, without random tile rotation.
            o.location=Vector((x,y,rz(x,y)))+normal*(.038+.003*(.5+.5*math.sin(col*2.1+row)))
            o['stage']='Roof tiles; no UV';o['row']=row
            bpy.context.view_layer.update()
            corners=[o.matrix_world@Vector(c) for c in o.bound_box]
            for poly,mask in masks:
                minx,maxx=min(p[0] for p in poly),max(p[0] for p in poly);miny,maxy=min(p[1] for p in poly),max(p[1] for p in poly)
                if max(c.x for c in corners)<minx or min(c.x for c in corners)>maxx or max(c.y for c in corners)<miny or min(c.y for c in corners)>maxy:continue
                if all(inside(c.x,c.y,poly) for c in corners):
                    bpy.data.objects.remove(o,do_unlink=True);o=None;break
                # Make only boundary tiles unique. All normal tiles stay shared instances.
                o.data=o.data.copy();active(o)
                m=o.modifiers.new('Cut to flashing','BOOLEAN');m.operation='DIFFERENCE';m.solver='EXACT';m.object=mask
                bpy.ops.object.modifier_apply(modifier=m.name);cut_count+=1
                if not o.data.polygons:bpy.data.objects.remove(o,do_unlink=True);o=None;break
for poly,o in masks:bpy.data.objects.remove(o,do_unlink=True)

# Dormer tiles follow the existing hood exactly. They are deformed only here.
def hz(x):
    for (a,z),(b,w) in zip(profile,profile[1:]):
        if a-1e-7<=x<=b+1e-7:return z+(w-z)*(x-a)/(b-a)
    return profile[0 if x<profile[0][0] else -1][1]
def endy(x):
    for (a,y),(b,z) in zip(joint,joint[1:]):
        if a-1e-7<=x<=b+1e-7:return y+(z-y)*(x-a)/(b-a)
    return joint[0 if x<joint[0][0] else -1][1]
for sign in [-1,1]:
    for row in range(5):
        outer=.70-row*.14;inner=max(.012,outer-.205)
        for col in range(7):
            vv=[];ff=[]
            for j in range(5):
                t=j/4;x=.52+sign*(outer+(inner-outer)*t)
                for i in range(4):
                    u=i/3;f=(col+.025+u*.95)/7
                    y=-2.30+(endy(x)+2.30)*f
                    z=hz(x)+.025*(y+2.27)/(endy(x)+2.27)+.047+.018*(1-t)+.010*math.sin(math.pi*u)
                    vv.append((x,y,z))
            for j in range(4):
                for i in range(3):
                    k=j*4+i;ff.append((k,k+1,k+5,k+4))
            if sign<0:ff=[tuple(reversed(f)) for f in ff]
            solid(f'SM_DormerTile_{sign}_{row}_{col}',vv,ff,dormer,.030)

# Half-round ridge modules, a shared hollow cross-section with a real underside.
old=bpy.data.objects.get('SM_Roof_Ridge_A')
if old:bpy.data.objects.remove(old,do_unlink=True)
vv=[];ff=[]
for x in [-.205,.205]:
    for i in range(13):
        a=math.pi*i/12;vv.append((x,.205*math.cos(a),.205*math.sin(a)))
for i in range(12):ff.append((i,i+1,i+14,i+13))
cap=solid('SM_Roof_RidgeCap_Shared_A',vv,ff,lib,.04)
for i in range(20):
    x=-3.52+i*7.04/19;o=cap.copy();o.data=cap.data;ridge.objects.link(o);o.name=f'SM_RidgeCap_{i:02}'
    o.location=(x,0,rz(x,0)+.025);o.rotation_euler.y=-math.atan((rz(x+.01,0)-rz(x-.01,0))/.02)
# Small segmented ridge for the dormer, supported by its existing hood.
for i in range(7):
    y=-2.26+(i+.5)*(endy(.52)+2.26)/7
    o=cap.copy();o.data=cap.data;ridge.objects.link(o);o.name=f'SM_Dormer_RidgeCap_{i:02}'
    o.scale=(.78,.46,.46);o.rotation_euler.z=math.pi/2
    o.location=(.52,y,hz(.52)+.025*(y+2.27)/(endy(.52)+2.27)+.045)

# Validate just this change; keep the previous geometry report separate.
bpy.context.view_layer.update();tileobjs=list(main.objects)+list(dormer.objects)+list(ridge.objects)
bad=[];triangles=0
for o in tileobjs:
    me=o.data;me.calc_loop_triangles();triangles+=len(me.loop_triangles)
    if any(t.area<1e-10 for t in me.loop_triangles):bad.append(o.name)
report={'revision':args.revision,'main_tiles':len(main.objects),'dormer_tiles':len(dormer.objects),'ridge_caps':len(ridge.objects),'shared_main_templates':len(cache),'boundary_boolean_operations':cut_count,'added_triangles':triangles,'degenerate_objects':bad,'stage':'Geometry prototype: no UV/materials/LOD/engine export'}
(ROOT/'QA'/('roof_'+args.revision+'.json')).write_text(json.dumps(report,indent=2),encoding='utf-8')
if bad:raise RuntimeError(bad)
s.camera=bpy.data.objects['CAM_01_Hero_Front_Left']
bpy.ops.object.select_all(action='DESELECT');bpy.ops.wm.save_as_mainfile(filepath=str(out/'House_Cottage_A.blend'))
shutil.copy2(__file__,out/Path(__file__).name)
print('ROOF_SAVED',report,flush=True)
st=bpy.data.collections['90_STUDIO - not exported']
close=camera('CAM_Tiled_Roof',(7,-11,9),(.1,-.65,4.45),7.9,st)
render(s,s.camera,rend/'01_Hero.png',1000)
render(s,close,rend/'02_Roof_Close.png',1000)
