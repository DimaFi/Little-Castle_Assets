"""Grey yard kit in independent modules. Never modifies old cottage/tree/prop files.
Run Blender -b --factory-startup --python this_file. One resumable generated batch.
"""
import sys,math,json,shutil,argparse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from kit_geometry import *
parser=argparse.ArgumentParser();parser.add_argument('--revision',default='v002')
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
assert args.revision.isalnum()
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'Source/Yard'/args.revision;REND=ROOT/'Renders/Yard'/args.revision
if (OUT/'Cottage_Yard_Kit.blend').exists():raise FileExistsError(OUT)
OUT.mkdir(parents=True,exist_ok=True);REND.mkdir(parents=True,exist_ok=True)
s,mat=setup();s.name='Cottage_Yard_Gallery'
assets=[]
def asset(name):
    c=collection(name);assets.append(c);return c
def B(name,loc,size,c,bevel=.014):return box(name,loc,size,c,mat,min(bevel,min(size)*.25))
def beam2(name,a,b,w,c):return bowed_beam(name,a,b,w,c,mat,min(.016,w*.10))
def cyl(name,a,b,r,c,n=14,r2=None):return cylinder(name,a,b,r,c,mat,n,r2)
def ring(name,z,r,h,c):return lathe(name,[(r,z-h/2),(r,z+h/2),(r-.026,z+h/2),(r-.026,z-h/2)],c,mat)

# Reuse roof meshes from the house. A local copy keeps the house library intact.
with bpy.data.libraries.load(str(ROOT/'Source/Openings/v007/House_Cottage_A.blend'),link=False) as (a,b):
    b.objects=['SM_RoofTile_Shared_0','SM_Roof_RidgeCap_Shared_A']
tile,cap=b.objects
templates=collection('SOURCE_SHARED_TEMPLATES');templates.hide_render=True;templates.hide_viewport=True
for o in [tile,cap]:
    templates.objects.link(o);o.data=o.data.copy();o.data.materials.clear();o.data.materials.append(mat)

def roof(c,width,depth,eave,rise):
    def z(x,y):
        t=abs(y)/(depth/2)
        return eave+rise*(1-t)-.045*(1-(x/(width/2))**2)+.065*t*t
    for side in [-1,1]:
        vv=[];ff=[];nx=12;ny=6
        for i in range(nx+1):
            x=-width/2+width*i/nx
            for j in range(ny+1):
                y=side*depth*j/(2*ny);vv.append((x,y,z(x,y)))
        for i in range(nx):
            for j in range(ny):
                k=i*(ny+1)+j;f=(k,k+ny+1,k+ny+2,k+1);ff.append(f if side>0 else f[::-1])
        o=mesh('Roof_Shell',vv,ff,c,mat);o.modifiers.new('Roof thickness','SOLIDIFY').thickness=.07
        beam('Eave',[(x,side*depth/2,z(x,side*depth/2)-.02) for x in [-width/2+i*width/12 for i in range(13)]],.11,.12,c,mat)
        rows=math.ceil((depth/2)/.25);columns=math.ceil(width/.30)
        for row in range(rows):
            yy=side*(depth/2-row*(depth/2-.09)/max(1,rows-1))
            for col in range(columns):
                x=-width/2+(col+.5)*width/columns
                dy=(z(x,yy+.001)-z(x,yy-.001))/.002;dx=(z(x+.001,yy)-z(x-.001,yy))/.002
                up=Vector((0,-side,-side*dy)).normalized();normal=Vector((-dx,-dy,1)).normalized();across=up.cross(normal).normalized()
                o=tile.copy();o.data=tile.data;c.objects.link(o);o.name='Roof_Tile'
                o.rotation_euler=Matrix((across,up,normal)).transposed().to_euler()
                o.scale.x=(width/columns-.008)/.320
                o.scale.y=min(1,(abs(yy)*math.sqrt(1+dy*dy)+.08)/.52)
                o.location=Vector((x,yy,z(x,yy)))+normal*.032
    for x in [-width/2,width/2]:
        for side in [-1,1]:beam('Verge',[(x,side*depth*i/16,z(x,side*depth*i/16)-.025) for i in range(9)],.10,.12,c,mat)
    n=math.ceil(width/.34)
    for i in range(n):
        x=-width/2+(i+.5)*width/n;o=cap.copy();o.data=cap.data;c.objects.link(o);o.name='Roof_RidgeCap';o.scale=(width/n/.37,.70,.70);o.location=(x,0,z(x,0)+.015)

def log(c,loc,r=.135,length=1.25,index=0):
    # Gentle taper and broad section variation; one actual cylinder per log.
    x,y,z=loc;n=11;vv=[]
    for j in range(4):
        t=j/3
        for i in range(n):
            a=i*2*math.pi/n;rr=r*(1-.07*t)*(.97+.05*math.sin(i*2.1+index))
            vv.append((x+rr*math.cos(a)+.01*math.sin(t*math.pi),y+length*t,z+rr*math.sin(a)))
    ff=[tuple(range(n-1,-1,-1)),tuple(range(3*n,4*n))]
    for j in range(3):
        for i in range(n):ff.append((j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i))
    mesh('Log_Bark',vv,ff,c,mat,.008)
    cyl('Log_CutEnd',(x,y-.008,z),(x,y-.018,z),r*.86,c,11)

def logstack(c,width=2.35,rows=4,length=1.35):
    for row in range(rows):
        n=8-row
        for i in range(n):log(c,((i-(n-1)/2)*.28,-length/2,.16+row*.245),.135,length,i+row*7)

c=asset('SM_Woodshed_A')
for x in [-1.4,1.4]:
    for y in [-.90,.90]:
        B('Stone_Foot',(x,y,.10),(.30,.30,.20),c,.035)
        beam2('Post',(x,y,.18),(x,y,2.10),.15,c)
for y in [-.90,.90]:
    beam2('Header',(-1.46,y,2.04),(1.46,y,2.04),.17,c)
    for x in [-1.4,1.4]:beam2('Brace',(x,y,1.55),(x-math.copysign(.48,x),y,2.02),.095,c)
for x in [-1.4,1.4]:
    beam2('Side_Tie',(x,-.9,2.02),(x,.9,2.02),.14,c)
    beam2('Gable_Kingpost',(x,0,2.03),(x,0,2.85),.12,c)
for i in range(14):B('Back_Board',(-1.30+i*.20,.94,1.05),(.188,.07,1.78),c)
for x in [-1.43,1.43]:
    for i in range(7):B('Side_Board',(x,-.64+i*.24,.82),(.07,.226,1.28),c)
roof(c,3.25,2.25,2.12,.79);logstack(c)

c=asset('SM_LogStack_A');logstack(c,rows=3,length=.90)

c=asset('SM_Well_A')
for row in range(3):
    for i in range(12):
        a=(i+(row%2)*.5)*2*math.pi/12+.012;b=a+2*math.pi/12-.024;vv=[]
        for z in [row*.25+.012,row*.25+.247]:
            for r in [.46,.71]:
                for j in range(4):
                    t=a+(b-a)*j/3;vv.append((r*math.cos(t),r*math.sin(t),z))
        ff=[]
        for j in range(3):ff.extend([(j,j+1,j+5,j+4),(j+8,j+12,j+13,j+9),(j,j+8,j+9,j+1),(j+4,j+5,j+13,j+12)])
        ff.extend([(0,4,12,8),(3,11,15,7)])
        mesh('Well_Stone',vv,ff,c,mat,.023)
for x in [-.90,.90]:
    beam2('Well_Post',(x,0,.03),(x,0,2.13),.14,c)
    for sign in [-1,1]:beam2('Well_Brace',(x,0,1.74),(x,sign*.40,2.15),.08,c)
beam2('Well_Crosshead',(-1.04,0,2.20),(1.04,0,2.20),.14,c)
cyl('Windlass',(-1.02,0,1.62),(1.09,0,1.62),.10,c,16)
beam2('Crank_Arm',(1.14,0,1.62),(1.14,0,1.31),.055,c)
cyl('Crank_Grip',(1.11,0,1.30),(1.37,0,1.30),.040,c,12)
tube('Rope_Winding',[( -.13+i*.0065,.12*math.cos(i*.25),1.62+.12*math.sin(i*.25)) for i in range(41)],.015,c,mat,6)
cyl('Well_Rope',(0,-.12,.16),(0,-.12,1.63),.016,c,8)
roof(c,2.35,1.8,2.23,.57)

def staved(c,name,height,base_radius,bulge,segments=16,open_top=True):
    levels=[0,height*.14,height*.50,height*.86,height]
    radii=[base_radius,base_radius+bulge*.65,base_radius+bulge,base_radius+bulge*.65,base_radius]
    for i in range(segments):
        a=i*2*math.pi/segments+.006;b=(i+1)*2*math.pi/segments-.006;vv=[]
        for inner in [False,True]:
            for z,r in zip(levels,radii):
                r-=.035 if inner else 0
                vv.extend([(r*math.cos(a),r*math.sin(a),z),(r*math.cos(b),r*math.sin(b),z)])
        ff=[]
        for j in range(4):
            k=2*j;ff.extend([(k,k+1,k+3,k+2),(k+10,k+12,k+13,k+11),(k,k+2,k+12,k+10),(k+1,k+11,k+13,k+3)])
        ff.extend([(0,10,11,1),(8,9,19,18)])
        mesh(name+'_Stave',vv,ff,c,mat,.005)
    cyl(name+'_Floor',(0,0,.025),(0,0,.065),base_radius-.03,c,segments)
    if not open_top:cyl(name+'_Lid',(0,0,height-.045),(0,0,height-.015),base_radius-.014,c,segments)
    return radii
c=asset('SM_Barrel_A');staved(c,'Barrel',.88,.285,.065,16,False)
for z,r in [(.12,.333),(.44,.36),(.76,.333)]:ring('Barrel_Hoop',z,r,.045,c)
c=asset('SM_Bucket_A');staved(c,'Bucket',.32,.145,.025,12)
for z,r in [(.06,.164),(.275,.164)]:ring('Bucket_Hoop',z,r,.022,c)
tube('Bucket_Handle',[(.18*math.cos(t),0,.30+.24*math.sin(t)) for t in [i*math.pi/20 for i in range(21)]],.012,c,mat)

c=asset('SM_WoodBench_A')
for y in [-.105,.105]:B('Seat_Board',(0,y,.48),(1.42,.196,.075),c,.018)
for x in [-.52,.52]:
    for y in [-.14,.14]:beam2('Bench_Leg',(x,y*1.15,.02),(x,y,.445),.085,c)
    beam2('Bench_SeatSupport',(x,-.24,.395),(x,.24,.395),.08,c)
beam2('Bench_Stretcher',(-.56,0,.22),(.56,0,.22),.07,c)
c=asset('SM_WoodTable_A')
for i in range(4):B('Tabletop_Board',(0,-.29+i*.194,.80),(1.30,.185,.065),c,.016)
for x in [-.49,.49]:
    for y in [-.27,.27]:beam2('Table_Leg',(x*1.07,y*1.07,.02),(x,y,.77),.085,c)
for y in [-.27,.27]:B('Table_Apron',(0,y,.68),(1.07,.065,.14),c)
beam2('Table_Stretcher',(-.50,0,.26),(.50,0,.26),.07,c)

c=asset('SM_FlowerBox_A')
for y in [-.205,.205]:
    for z in [.11,.25]:B('Planter_LongBoard',(0,y,z),(1.14,.047,.133),c)
for x in [-.55,.55]:
    for z in [.11,.25]:B('Planter_EndBoard',(x,0,z),(.05,.4,.133),c)
    for y in [-.21,.21]:B('Planter_CornerStrap',(x,y,.18),(.065,.070,.36),c)
B('Planter_Base',(0,0,.045),(1.12,.42,.07),c)
B('Planter_Soil',(0,0,.245),(1.03,.345,.055),c,.02)
# Reuse existing flowers instead of authoring another vegetation system.
with bpy.data.libraries.load(str(ROOT.parents[0]/'Vegetation/Oak_Kit/Cozy_Oak_Kit.blend'),link=False) as (a,b):
    b.objects=['SM_FlowerCluster_A','SM_FlowerCluster_B','SM_GroundPlant_A']
plants=b.objects
for o in plants:
    templates.objects.link(o);o.data=o.data.copy();o.data.materials.clear();o.data.materials.append(mat)
    for poly in o.data.polygons:poly.material_index=0
for i,x in enumerate([-.37,0,.37]):
    src=plants[i%2];o=src.copy();o.data=src.data;c.objects.link(o);o.name='Planter_Flowers';o.location=(x,0,.27);o.scale=(.65,.65,.65)
for x in [-.2,.22]:
    o=plants[2].copy();o.data=plants[2].data;c.objects.link(o);o.name='Planter_Leaves';o.location=(x,-.03,.27);o.scale=(.7,.7,.7)

c=asset('SM_Pot_A')
lathe('Pot_Body',[(.12,.01),(.17,.05),(.215,.28),(.20,.36),(.218,.37),(.218,.40),(.18,.40),(.178,.36),(.15,.09),(.08,.06)],c,mat)
c=asset('SM_Crate_A')
for y in [-.265,.265]:
    for z in [.12,.29,.46]:B('Crate_LongSlat',(0,y,z),(.62,.045,.15),c)
for x in [-.287,.287]:
    for z in [.12,.29,.46]:B('Crate_EndSlat',(x,0,z),(.045,.51,.15),c)
    for y in [-.23,.23]:B('Crate_Corner',(x,y,.29),(.06,.06,.52),c)
for i in range(3):B('Crate_Lid',(0,-.172+i*.172,.55),(.62,.16,.045),c)
B('Crate_Bottom',(0,0,.045),(.60,.52,.055),c)
beam2('Crate_Diagonal',(-.26,-.299,.075),(.26,-.299,.515),.060,c)

c=asset('SM_FenceBay_A')
for x in [-1,1]:
    beam2('Fence_Post',(x,0,0),(x,0,1.16),.14,c)
    B('Fence_PostCap',(x,0,1.18),(.18,.18,.055),c)
for z in [.43,.87]:B('Fence_Rail',(0,.035,z),(2.07,.085,.12),c)
c=asset('SM_Gate_A')
root=root_empty('CTRL_Gate_Hinge',c,(-.50,0,.1))
parts=[]
for i in range(6):
    x=-.42+i*.168;h=.94+.07*math.cos(x*math.pi/.92)
    parts.append(B('Gate_Picket',(x,0,.1+h/2),(.154,.085,h),c))
for z in [.33,.79]:parts.append(B('Gate_CrossRail',(0,.070,z),(1.03,.07,.105),c))
parts.append(beam2('Gate_Diagonal',(-.44,.095,.29),(.44,.095,.84),.075,c))
parts.append(tube('Gate_RingHandle',[(.32+.047*math.cos(t),-.073,.61+.047*math.sin(t)) for t in [i*2*math.pi/24 for i in range(25)]],.01,c,mat))
parent_world(parts,root)
for z in [.33,.79]:
    o=B('Gate_HingeStrap',(-.36,-.060,z),(.32,.022,.043),c,.005);parent_world([o],root)

c=asset('SM_StoneWall_A')
for row in range(3):
    start=-1.05;segments=4 if row%2==0 else 5
    sizes=[.525]*4 if row%2==0 else [.2625,.525,.525,.525,.2625]
    for i,length in enumerate(sizes):
        B('Wall_Stone',(start+length/2,0,.12+row*.235),(length-.015,.34+.012*math.sin(i*2+row),.227),c,.045);start+=length
c=asset('SM_Stump_Axe_A')
cyl('Stump',(0,0,.015),(0,0,.47),.27,c,13,.23)
cyl('Stump_Cut',(0,0,.462),(0,0,.480),.213,c,13)
beam2('Axe_Handle',(.03,0,.40),(.31,0,1.03),.037,c)
prism('Axe_Head',[(.15,.89),(.21,1.00),(.50,.93),(.47,.81)],-.037,.037,c,mat,.009)

c=asset('SM_Birdhouse_A')
with bpy.data.libraries.load(str(ROOT.parents[0]/'Props/Birdhouse_01.blend'),link=False) as (a,b):b.objects=['SM_Birdhouse_01']
o=b.objects[0];c.objects.link(o);o.data=o.data.copy();o.data.materials.clear();o.data.materials.append(mat)
for face in o.data.polygons:face.material_index=0
bm=bmesh.new();bm.from_mesh(o.data)
bmesh.ops.dissolve_degenerate(bm,dist=1e-6,edges=list(bm.edges));bm.to_mesh(o.data);bm.free();o.data.update()
o.location.z=.22

c=asset('SM_Signpost_A');beam2('Sign_Post',(0,0,0),(0,0,1.42),.10,c)
prism('Sign_Arrow',[(-.47,1.05),(.35,1.05),(.51,1.18),(.35,1.31),(-.47,1.31)],-.075,.005,c,mat,.016)

c=asset('SM_Wheelbarrow_A')
for y in [-.31,.31]:
    B('Barrow_Side',(0,y,.66),(.88,.055,.30),c)
    beam2('Barrow_Handle',(-.53,y,.46),(.98,y,.50),.065,c)
for x in [-.44,.44]:B('Barrow_End',(x,0,.66),(.055,.63,.30),c)
B('Barrow_Floor',(0,0,.49),(.88,.62,.065),c)
for y in [-.27,.27]:beam2('Barrow_Leg',(.30,y,.46),(.42,y,.04),.065,c)
cyl('Barrow_Axle',(-.58,-.23,.24),(-.58,.23,.24),.042,c)
wheel=lathe('Barrow_Wheel',[(.25,-.07),(.25,.07),(.19,.07),(.19,-.07)],c,mat,20)
wheel.rotation_euler.x=math.pi/2;wheel.location=(-.58,0,.25)
for i in range(6):
    a=i*math.pi/3;beam2('Barrow_Spoke',(-.58,0,.25),(-.58+.21*math.cos(a),0,.25+.21*math.sin(a)),.038,c)

# Each collection becomes a native standalone scene, with its own saved camera.
st=studio(s,mat);bpy.data.objects['Studio ground'].location.z=-.125
manifest=[];gallery=collection('YARD_GALLERY')
gallery_slots=[]
for index,c in enumerate(assets):
    for o in c.all_objects:
        if o.type=='MESH':o['stage']='Grey geometry kit; UV/materials/LOD pending'
    lo,hi=bounds(list(c.all_objects));dims=[hi[i]-lo[i] for i in range(3)]
    stats=inspect_geometry(list(c.all_objects));stats.update({'name':c.name,'dimensions_m':dims,'bounds_min_m':lo,'bounds_max_m':hi})
    manifest.append(stats)
    assert not stats['issues'],(c.name,stats['issues'])
    sc=bpy.data.scenes.new(c.name);sc.unit_settings.system='METRIC';sc.unit_settings.scale_length=1
    sc.collection.children.link(c);sc.collection.children.link(st);sc.world=s.world
    sc.render.engine='CYCLES';sc.cycles.samples=16;sc.cycles.use_denoising=True;sc.render.threads_mode='FIXED';sc.render.threads=8
    sc.view_settings.view_transform='AgX'
    target=Vector([(hi[i]+lo[i])/2 for i in range(3)])
    cam=camera('CAM_'+c.name,target+Vector((4,-6,3.5)),target,max(dims)*1.75,st);sc.camera=cam
    s.collection.children.unlink(c)
    instance=bpy.data.objects.new('INSTANCE_'+c.name,None);instance.instance_type='COLLECTION';instance.instance_collection=c
    gallery.objects.link(instance);instance.location=((index%5)*4.6,(index//5)*4.5,0);gallery_slots.append(instance)
    folder=OUT/'Modules'/c.name;folder.mkdir(parents=True,exist_ok=True)
    # Scene datablock makes this an openable .blend, not only an Append library.
    bpy.data.libraries.write(str(folder/(c.name+'.blend')),{sc},fake_user=True)
    bpy.context.window.scene=sc
    render(sc,cam,REND/(c.name+'.png'),560)
    print('YARD_MODULE_SAVED',c.name,stats['triangles'],flush=True)

bpy.context.window.scene=s
cam=camera('CAM_Yard_Gallery',(24,-18,22),(9,6,0),27,st);s.camera=cam
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Cottage_Yard_Kit.blend'))
shutil.copy2(__file__,OUT/Path(__file__).name)
(ROOT/'QA'/('yard_'+args.revision+'.json')).write_text(json.dumps({'modules':manifest,'asset_count':len(assets),'reuse':['Roof tiles and ridge caps from House v007','Flowers and ground plant from Oak_Kit','Birdhouse_01']},indent=2),encoding='utf-8')
print('YARD_KIT_COMPLETE',len(assets),flush=True)
