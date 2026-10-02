"""Door and operable shutters. Read v006, preserve it, write Openings/v007."""
import sys, math, json, shutil
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from kit_geometry import *
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'Source/Openings/v007';renders=ROOT/'Renders/Checkpoint_04/v007'
if (out/'House_Cottage_A.blend').exists():raise FileExistsError(out)
out.mkdir(parents=True,exist_ok=True);renders.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Source/Roof/v006/House_Cottage_A.blend'))
s=bpy.context.scene;mat=bpy.data.materials['M_Blockout_Grey']
D=bpy.data.collections['08_DOORS'];W=bpy.data.collections['07_WINDOWS']
doorold=bpy.data.objects['SM_Door_Main_A'];hinge=doorold.location.copy()
bpy.data.objects.remove(doorold,do_unlink=True)
doorcol=collection('DOOR_LEAF - rotate CTRL at hinge',D);parts=[]
cx=.8;bottom=.39;width=1.02;spring=bottom+2.05-width/2
for i in range(6):
    a=cx-width/2+i*width/6+.003;b=cx-width/2+(i+1)*width/6-.003
    top=[(b+(a-b)*j/5,spring+math.sqrt(max(0,(width/2)**2-(b+(a-b)*j/5-cx)**2))) for j in range(6)]
    o=prism('SM_Door_Plank_A',[(a,bottom),(b,bottom)]+top,-2.325,-2.20,doorcol,mat,.010);parts.append(o)
for z in [.82,1.75]:
    parts.append(box('SM_Door_IronStrap_A',(.68,-2.353,z),(.76,.035,.075),doorcol,mat,.013))
    for x in [.34,1.0]:parts.append(cylinder('SM_Door_Rivet_A',(x,-2.38,z),(x,-2.356,z),.018,doorcol,mat,8))
    cylinder('SM_Door_HingeBarrel_A',(.29,-2.36,z-.08),(.29,-2.36,z+.08),.038,D,mat,12)
parts.append(box('SM_Door_HandlePlate_A',(1.115,-2.36,1.2),(.10,.028,.17),doorcol,mat,.008))
parts.append(tube('SM_Door_RingHandle_A',[(1.115+.067*math.cos(t),-2.40,1.155+.067*math.sin(t)) for t in [i*2*math.pi/28 for i in range(29)]],.012,doorcol,mat))
for z in [.76,1.80]:parts.append(box('SM_Door_BackBrace_A',(.8,-2.18,z),(.94,.06,.12),doorcol,mat,.016))
ctrl=root_empty('CTRL_Door_Main_A',doorcol,hinge);ctrl['operation']='Rotate local Z; assembled closed angle 0 degrees'
parent_world(parts,ctrl)

shutter_count=0
for old in list(W.objects):
    if not old.name.startswith('SM_Shutter_'):continue
    label=old.name.removeprefix('SM_Shutter_');bpy.context.view_layer.update();matrix=old.matrix_world.copy()
    lo=[min(v.co[i] for v in old.data.vertices) for i in range(3)];hi=[max(v.co[i] for v in old.data.vertices) for i in range(3)]
    bpy.data.objects.remove(old,do_unlink=True)
    col=collection('SHUTTER_'+label,W);root=root_empty('CTRL_Shutter_'+label,col);root.matrix_world=matrix
    root['operation']='Rotate local Z at hinge. 0 = current open facade pose.'
    w=hi[0]-lo[0];h=hi[2]-lo[2];midy=(hi[1]+lo[1])/2
    for i in range(3):
        o=box('SM_Shutter_Plank_'+label,(lo[0]+(i+.5)*w/3,midy,(lo[2]+hi[2])/2),(w/3-.005,hi[1]-lo[1],h),col,mat,.012);o.parent=root
    for t in [.22,.78]:
        z=lo[2]+h*t
        o=box('SM_Shutter_CrossBrace_'+label,((lo[0]+hi[0])/2,lo[1]-.024,z),(w*.91,.048,.065),col,mat,.010);o.parent=root
        # Two sturdy hinge straps are sufficient at game viewing distance.
        o=box('SM_Shutter_Hinge_'+label,((lo[0]+hi[0])/2,lo[1]-.053,z),(w*.8,.015,.027),col,mat,.005);o.parent=root
    shutter_count+=1

# Existing reusable lantern, preserved in Art/Props; this scene uses a grey copy.
details=bpy.data.collections['09_DETAILS'];lampcol=collection('WALL_LANTERN',details)
with bpy.data.libraries.load(str(ROOT.parents[0]/'Props/Lantern_01.blend'),link=False) as (a,b):b.objects=['SM_Lantern_01']
lamp=b.objects[0];lampcol.objects.link(lamp);lamp.name='SM_House_WallLantern_A'
lamp.data=lamp.data.copy();lamp.data.materials.clear();lamp.data.materials.append(mat)
for face in lamp.data.polygons:face.material_index=0
lamp.location=(-.19,-2.90,2.55)
box('SM_Lantern_Backplate_A',(-.19,-2.46,2.4),(.12,.055,.35),lampcol,mat,.014)
tube('SM_Lantern_Bracket_A',[(-.19,-2.47,2.38),(-.19,-2.63,2.62),(-.19,-2.83,2.67),(-.19,-2.91,2.58),(-.19,-2.90,2.53)],.021,lampcol,mat)

# Make the overlap lips of the shared half-round caps readable in grey.
cap=bpy.data.objects['SM_Roof_RidgeCap_Shared_A']
for v in cap.data.vertices:
    f=1+.065*max(0,min(1,1-(v.co.x+.205)/.410))**4
    v.co.y*=f;v.co.z*=f

stats=inspect_geometry(list(doorcol.all_objects)+list(W.all_objects)+list(lampcol.objects))
stats.update({'shutter_controllers':shutter_count,'door_controller':ctrl.name,'reuse':'Art/Props/Lantern_01.blend; grey copy'})
assert not stats['issues'],stats['issues']
(ROOT/'QA/openings_v007.json').write_text(json.dumps(stats,indent=2),encoding='utf-8')
st=bpy.data.collections['90_STUDIO - not exported'];hero=bpy.data.objects['CAM_01_Hero_Front_Left']
doorcam=camera('CAM_Door_Detail',(3.5,-8,3.4),(.5,-2.45,1.48),3.5,st)
wincam=camera('CAM_Window_Detail',(-4,-7,2.6),(-1.56,-2.4,1.6),2.5,st)
s.camera=hero;bpy.ops.object.select_all(action='DESELECT');bpy.ops.wm.save_as_mainfile(filepath=str(out/'House_Cottage_A.blend'))
shutil.copy2(__file__,out/Path(__file__).name)
for name,cam in [('01_Hero',hero),('02_Door',doorcam),('03_Window',wincam)]:render(s,cam,renders/(name+'.png'),900)
print('OPENINGS_COMPLETE',stats,flush=True)
