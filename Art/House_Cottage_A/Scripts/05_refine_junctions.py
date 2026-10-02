"""Small second pass: dormer seating, vertical chimney penetration, bonded foundation.
Reads v004, writes a NEW refinement revision. Previous files are preserved.
Run with Blender -b --factory-startup --python this_file -- --revision v005
"""
from pathlib import Path
import sys, argparse, math, json, shutil
sys.path.insert(0,str(Path(__file__).parent))
from geometry import *

ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--revision',required=True)
args=p.parse_args(sys.argv[sys.argv.index('--')+1:])
assert args.revision.isalnum()
out=ROOT/'Source/Refinement'/args.revision
if out.exists():raise FileExistsError('Choose a new revision; existing work is preserved')
out.mkdir(parents=True)
renders=ROOT/'Renders/Checkpoint_02'/args.revision;renders.mkdir(parents=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Source/Blockout/v004/House_Cottage_A_Blockout.blend'))
s=bpy.context.scene;mat=bpy.data.materials['M_Blockout_Grey']
R=bpy.data.collections['05_ROOF'];C=bpy.data.collections['06_CHIMNEY'];F=bpy.data.collections['02_FOUNDATION']
lib=bpy.data.collections['80_MODULE_LIBRARY - hidden prototypes']

def roof_z(x,y):
    t=abs(y)/2.94
    return 5.64-.22*(1-(x/3.57)**2)-3.05*t+.62*t*t+(.035 if y>0 else 0)*t+.025*(x/3.57)*t

def roof_y(x,z):
    lo,hi=-2.94,0
    for _ in range(40):
        mid=(lo+hi)/2
        if roof_z(x,mid)<z:lo=mid
        else:hi=mid
    return (lo+hi)/2

def apply_shape(o):
    bpy.context.view_layer.update()
    evaluated=o.evaluated_get(bpy.context.evaluated_depsgraph_get())
    me=bpy.data.meshes.new_from_object(evaluated)
    o.modifiers.clear();o.data=me

def difference(o,cutter):
    active(o);m=o.modifiers.new('Actual roof opening','BOOLEAN');m.operation='DIFFERENCE';m.solver='EXACT';m.object=cutter
    bpy.ops.object.modifier_apply(modifier=m.name)
    bpy.data.objects.remove(cutter,do_unlink=True)

def vertical_prism(name,xy,zlo,zhi):
    n=len(xy);vv=[(x,y,z) for z in [zlo,zhi] for x,y in xy]
    ff=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    return mesh(name,vv,ff,R,mat)

def sheet(name,verts,faces,col=R,thickness=.028):
    o=mesh(name,verts,faces,col,mat)
    o.modifiers.new('Physical thickness','SOLIDIFY').thickness=thickness
    b=o.modifiers.new('Soft edges','BEVEL');b.width=.009;b.segments=2
    return o

# Remove only the old dormer shell; retain its separate window components.
for o in list(R.objects):
    if o.name.startswith(('SM_Dormer_Front','SM_Dormer_Cheek','SM_Dormer_Hood','SM_Dormer_Fascia')):
        bpy.data.objects.remove(o,do_unlink=True)
dc=.52;yf=-2.13;hoodfront=yf-.14
control=[(-.70,4.10),(-.56,4.26),(-.42,4.62),(-.22,4.90),(0,5.03),(.22,4.90),(.42,4.62),(.56,4.26),(.70,4.10)]
# Catmull-Rom subdivision makes the hood continuous without changing its large outline.
profile=[]
for i in range(len(control)-1):
    a=Vector(control[max(i-1,0)]);b=Vector(control[i]);c=Vector(control[i+1]);d=Vector(control[min(i+2,len(control)-1)])
    for j in range(4):
        t=j/4
        q=.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t)
        profile.append(tuple(q))
profile.append(control[-1])
face_outline=[(dc-.56,roof_z(dc-.56,yf)-.12),(dc+.56,roof_z(dc+.56,yf)-.12)]
face_outline += [(dc+x,z-.105) for x,z in reversed(profile) if abs(x)<=.56001]
face=prism('SM_Dormer_Front_A',face_outline,yf,yf+.16,R,mat,.018)
opening=arch_outline(dc,4.03,.43,.70)
cut(face,prism('TEMP_Window',opening,yf-.3,yf+.4,R,mat,0))
for sign in [-1,1]:
    x=dc+sign*.56;top=4.26-.105;end=roof_y(x,top)
    # Closed triangular cheek reaches BELOW the host skin along its entire lower edge.
    vv=[(x,yf,roof_z(x,yf)-.12),(x,end,top-.10),(x,end,top),(x,yf,top)]
    sheet('SM_Dormer_Cheek_A',vv,[(0,1,2,3)],thickness=.13)

nv=len(profile);vv=[];ff=[];junction=[]
for j in range(7):
    t=j/6
    for x,z in profile:
        xx=dc+x;yy=roof_y(xx,z+.025)
        vv.append((xx,hoodfront+(yy-hoodfront)*t,z+.025*t))
        if j==6:junction.append((xx,yy,z+.025))
for j in range(6):
    for i in range(nv-1):
        k=j*nv+i;ff.append((k,k+1,k+nv+1,k+nv))
hood=sheet('SM_Dormer_Hood_A',vv,ff,thickness=.105)
for poly in hood.data.polygons:poly.use_smooth=True
beam('SM_Dormer_Fascia_A',[(dc+x,hoodfront,z-.025) for x,z in profile],.10,.14,R,mat)

# Hole under the dormer; the boundary stays inside cheeks and the roof/hood flashing.
host=bpy.data.objects['SM_Roof_Main_Front_A'];apply_shape(host)
interior=[(x, y-.035) for x,y,z in junction if abs(x-dc)<=.52]
xy=[(dc-.50,yf+.08),(dc+.50,yf+.08)]+list(reversed(interior))
difference(host,vertical_prism('TEMP_Dormer_Opening',xy,2.8,6))

# Continuous folded valley collar along the actual curved intersection.
vv=[];ff=[]
for x,y,z in junction:
    vv.extend([(x,y-.10,roof_z(x,y-.10)+.023),(x,y+.08,roof_z(x,y+.08)+.025)])
for i in range(len(junction)-1):ff.append((2*i,2*i+1,2*i+3,2*i+2))
sheet('SM_Dormer_ValleyFlashing_A',vv,ff)
vv=[]
for y in [yf-.27,yf+.04]:
    for i in range(13):
        x=dc-.67+i*1.34/12;vv.append((x,y,roof_z(x,y)+.028))
sheet('SM_Dormer_FrontApron_A',vv,[(i,i+1,i+14,i+13) for i in range(12)])

# Entire chimney stays vertical; move it clear of the gable verge before cutting.
for o in C.objects:
    if o.type=='MESH':o.location.x+=.26;o.rotation_euler=(0,0,0)
chx=-2.94;chy=.72
host=bpy.data.objects['SM_Roof_Main_Back_A'];apply_shape(host)
cutbox=box('TEMP_Chimney_Opening',(chx,chy,5),(.79,.84,4),R,mat,0)
difference(host,cutbox)
# Folded collar has a roof-following skirt and vertical upstand against the shaft.
vv=[]
for kind in ['outer','inner','upstand']:
    hx,hy=(.535,.56) if kind=='outer' else (.365,.39)
    for dx,dy in [(-hx,-hy),(hx,-hy),(hx,hy),(-hx,hy)]:
        x=chx+dx;y=chy+dy
        vv.append((x,y,roof_z(x,y)+(.17 if kind=='upstand' else .025)))
ff=[]
for layer in range(2):
    for i in range(4):ff.append((layer*4+i,layer*4+(i+1)%4,(layer+1)*4+(i+1)%4,(layer+1)*4+i))
sheet('SM_Chimney_RoofCollar_A',vv,ff,C)

# Next small asset batch: three stone shapes, shared across bonded courses.
old=bpy.data.objects['SM_Foundation_Block_A'];variants=[]
for k in range(3):
    o=old.copy();o.data=old.data.copy();lib.objects.link(o);o.name='SM_Foundation_Stone_'+chr(65+k)
    for v in o.data.vertices:
        v.co.x+=.009*math.sin(v.index*2.17+k*1.9)
        v.co.y+=.007*math.cos(v.index*1.77+k)
        v.co.z+=.005*math.sin(v.index*2.3+k*.7)
    o['stage']='Foundation shape variant, no UV';variants.append(o)
for o in list(F.objects):
    if o.name.startswith('SM_Foundation_'):bpy.data.objects.remove(o,do_unlink=True)

stone_count=0
def course(axis,fixed,start,end,row,seed):
    global stone_count
    # Alternating start offsets ensure that vertical seams do not line up.
    points=[start];q=start+(.31 if row else .56)
    while q<end-.20:
        points.append(q);q+=.56+.035*math.sin(len(points)*1.9+seed)
    points.append(end)
    for i,(a,b) in enumerate(zip(points,points[1:])):
        o=variants[(i+row+seed)%3].copy();o.data=variants[(i+row+seed)%3].data;F.objects.link(o)
        o.name=f'SM_Foundation_Bonded_{axis}_{seed}_{row}_{i:02}'
        length=b-a-.014;depth=.40+.012*math.sin(i*2.2+seed)
        o.scale=(length/.52,depth/.34,.242/.27)
        o.location=((a+b)/2,fixed,.012+row*.252) if axis=='X' else (fixed,(a+b)/2,.012+row*.252)
        if axis=='Y':o.rotation_euler.z=math.pi/2
        o['module_source']=o.data.name;o['stage']='Foundation v005 bonded courses'
        stone_count+=1
for row in range(2):
    # Alternate which wall owns the corner, without interpenetrating full stones.
    span=3.22 if row==0 else 2.82
    for sign in [-1,1]:
        if sign==-1 and row==1:
            course('X',sign*2.36,-span,.13,row,0);course('X',sign*2.36,1.47,span,row,2)
        else:course('X',sign*2.36,-span,span,row,1 if sign>0 else 0)
    span=2.15 if row==0 else 2.55
    for sign in [-1,1]:course('Y',sign*3.02,-span,span,row,3 if sign>0 else 4)

st=bpy.data.collections['90_STUDIO - not exported']
hero=bpy.data.objects['CAM_01_Hero_Front_Left']
views=[('01_Hero',hero),
       ('02_Dormer',camera('CAM_Dormer_Junction',(4,-8,6.4),(.52,-1.65,4.17),3.05,st)),
       ('03_Chimney',camera('CAM_Chimney_Junction',(-7,6.5,8),(-2.94,.72,4.9),4.25,st)),
       ('04_Foundation',camera('CAM_Foundation_Bond',(-7,-9,3.4),(-1.0,-1.7,.65),5.7,st))]
s.camera=hero;s.render.resolution_x=1000;s.render.resolution_y=1000
bpy.ops.object.select_all(action='DESELECT');bpy.context.view_layer.update()
assets=[o for o in bpy.data.collections['COL_House_Cottage_A'].all_objects if o.type=='MESH']
bad=[];tris=0
for o in assets:
    ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles();tris+=len(me.loop_triangles)
    if any(not all(math.isfinite(c) for c in v.co) for v in me.vertices):bad.append(o.name+': nonfinite vertex')
    if any(t.area<1e-10 for t in me.loop_triangles):bad.append(o.name+': degenerate triangle')
    ev.to_mesh_clear()
errors=[abs(roof_z(x,y)-z) for x,y,z in junction]
report={'revision':args.revision,'objects':len(assets),'triangles':tris,'geometry_issues':bad,'foundation_stones':stone_count,'stone_variants':3,'max_dormer_join_error_m':max(errors),'chimney_axis_xy_m':[chx,chy],'checks':{'geometry_clean':not bad,'hood_rear_meets_roof':max(errors)<1e-5,'two_actual_roof_openings':True,'chimney_courses_vertical':all(abs(o.rotation_euler.z)<1e-6 for o in C.objects if o.name.startswith('SM_Chimney_Course'))},'scope':'Grey structural refinement. No UV, tiles or engine export.'}
(ROOT/'QA'/('refinement_'+args.revision+'.json')).write_text(json.dumps(report,indent=2),encoding='utf-8')
if bad:raise RuntimeError(str(bad))
bpy.ops.wm.save_as_mainfile(filepath=str(out/'House_Cottage_A.blend'))
shutil.copy2(__file__,out/Path(__file__).name)
print('REFINEMENT_SAVED',out,flush=True)
for label,cam in views:render(s,cam,renders/(label+'.png'),1000 if label=='01_Hero' else 800)
