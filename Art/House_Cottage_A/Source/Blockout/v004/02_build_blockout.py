"""Checkpoint 01: editable grey house built from small parts.
Source axes: X = facade width / roof ridge, front = -Y, Z up. Metres.
No production UV, textures, tile scatter, props, LODs or final collision.
All outputs go to a NEW revision directory; previous revisions stay intact.
"""
from pathlib import Path
import argparse, sys, json, math
sys.path.insert(0,str(Path(__file__).parent))
from geometry import *

ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--revision',required=True);p.add_argument('--skip-renders',action='store_true')
cfg=p.parse_args(sys.argv[sys.argv.index('--')+1:])
if not cfg.revision.replace('_','').isalnum():raise ValueError('Revision must be alphanumeric')
out=ROOT/'Source/Blockout'/cfg.revision
if out.exists(): raise FileExistsError('Revision already exists; use a new revision to preserve edits: '+str(out))
out.mkdir(parents=True)
rend=ROOT/'Renders/Checkpoint_01'/cfg.revision;rend.mkdir(parents=True,exist_ok=True)
s,mat=setup()
root=collection('COL_House_Cottage_A')
cols={n:collection(n,root) for n in ['00_REFERENCE','01_BLOCKOUT','02_FOUNDATION','03_WALLS','04_TIMBER','05_ROOF','06_CHIMNEY','07_WINDOWS','08_DOORS','09_DETAILS','10_COLLISION','11_LOD']}
F,W,T,R,C,WIN,D=[cols[n] for n in ['02_FOUNDATION','03_WALLS','04_TIMBER','05_ROOF','06_CHIMNEY','07_WINDOWS','08_DOORS']]
params={'width_m':6.2,'depth_m':4.8,'wall_base_m':.46,'wall_top_m':3.30,'roof_half_width_m':3.57,'roof_half_depth_m':2.94,'ridge_end_m':5.64,'ridge_sag_m':.22,'door_height_m':2.05,'door_width_m':1.02,'door_x_m':.8,'chimney_top_m':6.70}
(out/'parameters.json').write_text(json.dumps(params,indent=2),encoding='utf-8')

# Load the small module library without touching previous cottage/tree files.
lib=ROOT/'Source/Modules/v002/Cottage_A_Primitives.blend'
with bpy.data.libraries.load(str(lib),link=False) as (src,dst):dst.objects=['SM_Foundation_Block_A','SM_Beam_Vertical_A','SM_RoofTile_A']
library=collection('80_MODULE_LIBRARY - hidden prototypes')
for o in dst.objects:
    library.objects.link(o);o.data.materials.clear();o.data.materials.append(mat)
library.hide_render=True;library.hide_viewport=True
stone=next(o for o in dst.objects if o.name.startswith('SM_Foundation'))

def stone_instance(name,center,size,col,index=0):
    o=stone.copy();o.data=stone.data;col.objects.link(o);o.name=name
    o.location=(center[0],center[1],center[2]-size[2]/2)
    o.scale=(size[0]/.52,size[1]/.34,size[2]/.27)
    o.rotation_euler[2]=.012*math.sin(index*2.31)
    o['module_source']='SM_Foundation_Block_A';o['stage']='Blockout masonry rhythm'
    return o

# Foundation: two broad courses, not a monolithic texture box.
for row in range(2):
    z=.13+row*.255
    for side in [-1,1]:
        count=12
        for i in range(count):
            x=-2.85+i*5.7/(count-1)
            # Leave the upper course open below the door, above the 39 cm landing.
            if side == -1 and row == 1 and abs(x-.8) < .75:
                continue
            stone_instance(f'SM_Foundation_Facade_{side}_{row}_{i:02}',(x,side*2.36,z),(.505,.38,.245),F,i+row*7)
        for i in range(9):
            y=-2.04+i*.51
            stone_instance(f'SM_Foundation_Side_{side}_{row}_{i:02}',(side*3.01,y,z),(.38,.495,.245),F,i+row*11)

# Walls have real thickness and real punched openings; the interior is unfinished.
walls={}
for side,label in [(-1,'Front'),(1,'Back')]:
    walls[label]=box('SM_Wall_'+label+'_A',(0,side*2.28,1.88),(6.2,.24,2.84),W,mat,.035)
for side,label in [(-1,'Left'),(1,'Right')]:
    walls[label]=box('SM_Wall_'+label+'_A',(side*2.98,0,1.88),(.24,4.32,2.84),W,mat,.035)
for wall in walls.values():
    bpy.context.view_layer.update()
    bottom_corner = wall.matrix_world @ Vector(wall.bound_box[0])
    origin(wall,bottom_corner)
    wall['pivot']='Lower wall corner, metres'

def roof_z(x,y):
    t=abs(y)/2.94
    sag=.22*(1-(x/3.57)**2)
    # Concave kick at the eave, subtly unequal front/back pitch, bowed ridge.
    return 5.64-sag-3.05*t+.62*t*t+(.035 if y>0 else 0)*t+.025*(x/3.57)*t

# Separate bowed timber members. Main front beam sits below the long roof slope.
for x in [-3.01,3.01]:
    for y in [-2.36,2.36]:
        bowed_beam('SM_Beam_Corner_A',(x,y,.47),(x+.018,y,3.27),.19,T,mat)
for y in [-2.41,2.41]:
    bowed_beam('SM_Beam_Facade_Top_A',(-3.09,y,3.02),(3.09,y,3.02),.20,T,mat,-.035)
    for x in [-3.01,3.01]:
        toward=1 if x<0 else -1
        bowed_beam('SM_Beam_Facade_Brace_A',(x,y,2.23),(x+toward*.76,y,2.97),.14,T,mat,.008)
for x in [-3.18,3.18]:
    bowed_beam('SM_Beam_Gable_Tie_A',(x,-2.38,3.26),(x,2.38,3.26),.21,T,mat,-.03)
    bowed_beam('SM_Beam_Gable_Centre_A',(x,0,3.26),(x,0,roof_z(x,0)-.12),.19,T,mat)
    for side in [-1,1]:
        bowed_beam('SM_Beam_Gable_Brace_A',(x,0,3.31),(x,side*1.5,roof_z(x,side*1.5)-.15),.15,T,mat)

# Gable infill follows the roof profile exactly, rather than a straight triangle.
for x,label in [(-3.115,'Left'),(2.885,'Right')]:
    vv=[]
    for xx in [x,x+.23]:
        vv += [(xx,-2.4,3.25),(xx,2.4,3.25)]
        vv += [(xx,2.4-i*4.8/24,roof_z(xx,2.4-i*4.8/24)-.14) for i in range(25)]
    n=27;ff=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]
    ff += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    mesh('SM_Wall_Gable_'+label+'_A',vv,ff,W,mat,.018)

# Two thick smooth blockout roof shells. Tiles are deliberately deferred.
for side,label in [(-1,'Front'),(1,'Back')]:
    vv=[];ff=[];nx=24;ny=18
    for i in range(nx+1):
        x=-3.57+7.14*i/nx
        for j in range(ny+1):
            y=side*2.94*j/ny;vv.append((x,y,roof_z(x,y)))
    for i in range(nx):
        for j in range(ny):
            k=i*(ny+1)+j
            face=(k,k+ny+1,k+ny+2,k+1)
            ff.append(face if side>0 else tuple(reversed(face)))
    o=mesh('SM_Roof_Main_'+label+'_A',vv,ff,R,mat)
    for poly in o.data.polygons:poly.use_smooth=True
    so=o.modifiers.new('Heavy roof shell','SOLIDIFY');so.thickness=.14;so.offset=-1
    be=o.modifiers.new('Rounded roof perimeter','BEVEL');be.width=.035;be.segments=3
    o['roof_role']='Silhouette shell, to receive instanced tile rows after approval'
    origin(o,(-3.57,0,roof_z(-3.57,0)))
    points=[(-3.57+i*7.14/24,side*2.94,roof_z(-3.57+i*7.14/24,side*2.94)-.035) for i in range(25)]
    beam('SM_Roof_Eave_'+label+'_A',points,.19,.21,R,mat)
for x,label in [(-3.56,'Left'),(3.56,'Right')]:
    for side in [-1,1]:
        points=[(x,side*2.94*i/20,roof_z(x,side*2.94*i/20)-.035) for i in range(21)]
        beam('SM_Roof_Verge_'+label+'_A',points,.18,.19,R,mat)
beam('SM_Roof_Ridge_A',[(x,0,roof_z(x,0)+.07) for x in [-3.6+i*7.2/24 for i in range(25)]],.24,.24,R,mat)

# Door opening: 205 cm slab height from top landing, displaced to the right.
cx=.8;bottom=.39;dw=1.02;dh=2.05
outline=arch_outline(cx,bottom,dw,dh)
cutter=prism('TEMP_door_cut',outline,-2.65,-1.99,W,mat,0);cut(walls['Front'],cutter)
door=prism('SM_Door_Main_A',outline,-2.30,-2.18,D,mat,.018);origin(door,(cx-dw/2,-2.30,bottom));door['pivot']='Left hinge at landing level'
spring=bottom+dh-dw/2
for side in [-1,1]:
    for i in range(5):
        h=(spring-bottom)/5
        stone_instance('SM_Door_Jamb_A',(cx+side*(dw/2+.135),-2.47,bottom+(i+.5)*h),(.255,.31,h-.012),D,i)
for i in range(9):
    a=i*math.pi/9+.012;b=(i+1)*math.pi/9-.012;ri=dw/2;ro=ri+.26
    poly=[(cx+ri*math.cos(a),spring+ri*math.sin(a)),(cx+ro*math.cos(a),spring+ro*math.sin(a)),(cx+ro*math.cos(b),spring+ro*math.sin(b)),(cx+ri*math.cos(b),spring+ri*math.sin(b))]
    prism('SM_Door_StoneArch_A',poly,-2.64,-2.30,D,mat,.022)
for i in range(3):
    box('SM_Entrance_Step_A',(cx,-3.04+i*.25,.065+i*.13),(1.68-i*.12,.72,.13),F,mat,.04)

def window(label,wall,cx,y,bottom,width,height,side_rotation=0):
    """Front-facing local opening, optionally rotated around the world origin."""
    outline=arch_outline(cx,bottom,width,height)
    cutter=prism('TEMP_window_cut',outline,y-.5,y+.5,WIN,mat,0)
    if side_rotation:cutter.rotation_euler[2]=side_rotation
    cut(wall,cutter)
    objects=[]
    objects.append(prism('SM_Window_Recess_'+label,outline,y+.13,y+.18,WIN,mat,.018))
    spring=bottom+height-width/2
    for sign in [-1,1]:
        objects.append(box('SM_Window_Frame_'+label,(cx+sign*(width/2+.045),y-.04,(bottom+spring)/2),(.10,.16,spring-bottom+.04),WIN,mat,.016))
        if width>.5:
            shutter_width=width*.50
            o=box('SM_Shutter_'+label,(cx+sign*(width/2+.08+shutter_width/2),y-.09,bottom+height*.43),(shutter_width,.085,height*.86),WIN,mat,.026)
            origin(o,(cx+sign*(width/2+.08),y-.09,bottom));o['pivot']='Shutter hinge';objects.append(o)
    points=[(cx+(width/2+.045)*math.cos(math.pi*i/16),y-.04,spring+(width/2+.045)*math.sin(math.pi*i/16)) for i in range(17)]
    objects.append(beam('SM_Window_Arch_'+label,points,.115,.15,WIN,mat))
    objects.append(box('SM_Window_Sill_'+label,(cx,y-.09,bottom-.055),(width+.30,.35,.12),WIN,mat,.025))
    objects.append(bowed_beam('SM_Window_Mullion_'+label,(cx,y-.065,bottom),(cx,y-.065,bottom+height-.045),.055,WIN,mat,.003))
    objects.append(box('SM_Window_Crossbar_'+label,(cx,y-.065,bottom+height*.53),(width,.065,.05),WIN,mat,.008))
    if side_rotation:
        from mathutils import Matrix
        bpy.context.view_layer.update()
        rot=Matrix.Rotation(side_rotation,4,'Z')
        for o in objects:o.matrix_world=rot@o.matrix_world

window('Front_L',walls['Front'],-1.56,-2.43,1.03,.79,1.02)
window('Front_R',walls['Front'],2.37,-2.43,1.35,.36,.73)
# Side local -Y facade rotated clockwise to face world -X.
window('Left',walls['Left'],.93,-3.13,1.06,.95,1.09,-math.pi/2)
window('Right',walls['Right'],.30,-3.13,1.08,.96,1.1,math.pi/2)
# Rear: facing outward +Y, using a rotated front-facing local construction.
window('Back',walls['Back'],.85,-2.43,1.12,.76,1.12,math.pi)

# Dormer: small pointed, softly flared hood, centred over the entrance area.
dc=.52;yf=-2.13;yb=-.64
profile=[(-.70,4.10),(-.56,4.26),(-.42,4.62),(-.22,4.90),(0,5.03),(.22,4.90),(.42,4.62),(.56,4.26),(.70,4.10)]
outline=[(dc-.59,3.88),(dc+.59,3.88)]+[(dc+x,z-.10) for x,z in reversed(profile[1:-1])]
face=prism('SM_Dormer_Front_A',outline,yf,yf+.17,R,mat,.025)
for sign in [-1,1]:
    # Cheeks taper up into the host roof toward the rear.
    vv=[(dc+sign*.56,yf,3.89),(dc+sign*.56,yb,roof_z(dc+sign*.56,yb)-.07),(dc+sign*.40,yb,4.87),(dc+sign*.56,yf,4.40)]
    o=mesh('SM_Dormer_Cheek_A',vv,[(0,1,2,3)],R,mat)
    o.modifiers.new('Cheek thickness','SOLIDIFY').thickness=.12
vv=[(dc+x,y,z+.07*(y-yf)/(yb-yf)) for y in [yf-.14,yb] for x,z in profile]
ff=[(i,i+1,i+10,i+9) for i in range(8)]
o=mesh('SM_Dormer_Hood_A',vv,ff,R,mat)
o.modifiers.new('Hood thickness','SOLIDIFY').thickness=.12
be=o.modifiers.new('Hood softened edges','BEVEL');be.width=.025;be.segments=3
beam('SM_Dormer_Fascia_A',[(dc+x,yf-.14,z-.025) for x,z in profile],.10,.14,R,mat)
opening=arch_outline(dc,4.03,.43,.70)
cut(face,prism('TEMP_dormer_cut',opening,yf-.3,yf+.35,R,mat,0))
prism('SM_Dormer_Window_Recess_A',opening,yf+.1,yf+.15,WIN,mat,.012)
spring=4.03+.70-.43/2
beam('SM_Dormer_Window_Arch_A',[(dc+.26*math.cos(math.pi*i/16),yf-.025,spring+.26*math.sin(math.pi*i/16)) for i in range(17)],.075,.10,WIN,mat)
for sign in [-1,1]:bowed_beam('SM_Dormer_Window_Jamb_A',(dc+sign*.25,yf-.025,4.01),(dc+sign*.25,yf-.025,spring),.075,WIN,mat,.004)
box('SM_Dormer_Window_Sill_A',(dc,yf-.05,4.0),(.67,.25,.12),WIN,mat,.025)
bowed_beam('SM_Dormer_Window_Mullion_A',(dc,yf-.025,4.03),(dc,yf-.025,4.71),.04,WIN,mat,.002)

# Chimney outside left gable: broad base tapering into a tall narrow shaft.
chx=-3.20;chy=.72
for row in range(24):
    z=.14+row*.27
    width=.73+max(0,1-z/3.7)*.24
    depth=.78+max(0,1-z/3.7)*.20
    # Upper courses are hollow. The alternating ring keeps the cap opening real.
    if row%2==0:
        sizes=[(width,.24,.258),(width,.24,.258),(.24,depth-.48,.258),(.24,depth-.48,.258)]
        centers=[(chx,chy-depth/2+.12,z),(chx,chy+depth/2-.12,z),(chx-width/2+.12,chy,z),(chx+width/2-.12,chy,z)]
    else:
        sizes=[(.24,depth,.258),(.24,depth,.258),(width-.48,.24,.258),(width-.48,.24,.258)]
        centers=[(chx-width/2+.12,chy,z),(chx+width/2-.12,chy,z),(chx,chy-depth/2+.12,z),(chx,chy+depth/2-.12,z)]
    for i,(center,size) in enumerate(zip(centers,sizes)):stone_instance('SM_Chimney_Course_A',center,size,C,row*4+i)
for center,size in [((chx,chy-.35,6.58),(.94,.25,.24)),((chx,chy+.35,6.58),(.94,.25,.24)),((chx-.35,chy,6.58),(.24,.45,.24)),((chx+.35,chy,6.58),(.24,.45,.24))]:
    stone_instance('SM_Chimney_Top_A',center,size,C)

# Reference images packed into the .blend, kept out of renders and exports.
for idx,file in enumerate(['01_Cottage_Concept_Modules.png','02_Cottage_Views_Materials.png']):
    o=bpy.data.objects.new('REF_'+str(idx+1),None);cols['00_REFERENCE'].objects.link(o)
    o.empty_display_type='IMAGE';o.data=bpy.data.images.load(str(ROOT/'References'/file));o.data.pack()
    o.empty_display_size=10;o.location=(0,5+idx*.1,4);o.rotation_euler=(math.pi/2,0,0)
cols['00_REFERENCE'].hide_viewport=True;cols['00_REFERENCE'].hide_render=True

st=studio(s,mat)
views=[('01_Hero_Front_Left',(-10,-15,9)),('02_Front',(0,-20,3.1)),('03_Back',(0,20,3.1)),('04_Left',(-20,0,3.1)),('05_Right',(20,0,3.1)),('06_Top',(0,0,25)),('07_Front_Right',(10,-15,9)),('08_Back_Left',(-10,15,9)),('09_Back_Right',(10,15,9))]
cameras=[]
for label,pos in views:cameras.append((label,camera('CAM_'+label,pos,(0,0,3.1),10.3,st)))
s.camera=cameras[0][1]
# Preserve a clean usable first view in the saved UI.
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_perspective='CAMERA'
            area.spaces.active.shading.light='STUDIO';area.spaces.active.shading.color_type='MATERIAL'
            area.spaces.active.shading.show_cavity=True
assets=[o for c in cols.values() for o in c.objects if o.type=='MESH']
bpy.context.view_layer.update()
manifest=[]
for o in assets:
    ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles()
    manifest.append({'name':o.name,'collection':o.users_collection[0].name,'mesh':o.data.name,'triangles_evaluated':len(me.loop_triangles),'location_m':list(o.location),'dimensions_m':list(o.dimensions),'stage':o.get('stage','blockout')})
    ev.to_mesh_clear()
(ROOT/'QA'/('blockout_manifest_'+cfg.revision+'.json')).write_text(json.dumps({'parameters':params,'object_count':len(assets),'triangles':sum(o['triangles_evaluated'] for o in manifest),'objects':manifest},indent=2),encoding='utf-8')
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.wm.save_as_mainfile(filepath=str(out/'House_Cottage_A_Blockout.blend'))
# Save exact scripts with each revision for reproducibility.
import shutil
for file in ['02_build_blockout.py','geometry.py']:
    shutil.copy2(Path(__file__).parent/file,out/file)
print('BLOCKOUT_SAVED',out,flush=True)
if not cfg.skip_renders:
    for label,cam in cameras:
        bpy.data.objects['Studio ground'].hide_render=label in ['02_Front','03_Back','04_Left','05_Right']
        render(s,cam,rend/(label+'.png'),1100 if label.startswith('01_') else 720)
        print('CHECKPOINT_RENDER',label,flush=True)
