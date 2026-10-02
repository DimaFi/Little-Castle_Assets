"""Demonstration arrangement using independent module instances. No engine import."""
import sys,math,json,shutil
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from kit_geometry import *
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'Source/Assembly/v008';REND=ROOT/'Renders/Checkpoint_05/v008'
if (OUT/'Cottage_Courtyard.blend').exists():raise FileExistsError(OUT)
OUT.mkdir(parents=True,exist_ok=True);REND.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Source/Openings/v007/House_Cottage_A.blend'))
s=bpy.context.scene;mat=bpy.data.materials['M_Blockout_Grey'];bpy.data.objects['Studio ground'].location.z=-.125
manifest=json.loads((ROOT/'QA/yard_v002.json').read_text(encoding='utf-8'))
names=[m['name'] for m in manifest['modules']]
assert all(not m['issues'] for m in manifest['modules'])
with bpy.data.libraries.load(str(ROOT/'Source/Yard/v002/Cottage_Yard_Kit.blend'),link=False) as (a,b):b.collections=names
modules={c.name:c for c in b.collections}
sources=bpy.data.scenes.new('Yard_Module_Sources - prefer standalone files')
for c in modules.values():sources.collection.children.link(c)
yard=collection('COL_Courtyard_Placement');placements=[]
def put(name,loc,angle=0,scale=1):
    o=bpy.data.objects.new('PLACE_'+name,None);yard.objects.link(o);o.instance_type='COLLECTION';o.instance_collection=modules[name]
    o.location=loc;o.rotation_euler.z=math.radians(angle);o.scale=(scale,)*3
    o['source_file']='Source/Yard/v002/Modules/'+name+'/'+name+'.blend'
    placements.append({'module':name,'location_m':list(loc),'rotation_z_deg':angle,'scale':scale})
    return o
put('SM_Woodshed_A',(5.40,.75,0))
put('SM_Well_A',(-4.8,-3.5,0),-5)
put('SM_WoodBench_A',(-4.2,.0,0),90)
put('SM_WoodTable_A',(3.8,-3.4,0),-12)
put('SM_Barrel_A',(3.58,-1.65,0),7)
put('SM_Barrel_A',(6.98,1.18,0),-8)
put('SM_Crate_A',(6.85,-.63,0),-13)
put('SM_Bucket_A',(-3.87,-3.6,0),0)
put('SM_FlowerBox_A',(-1.56,-2.71,.57))
put('SM_FlowerBox_A',(2.64,-2.73,.02))
put('SM_Pot_A',(-.45,-3.15,0))
put('SM_Pot_A',(4.05,-.40,0),0,.85)
put('SM_Stump_Axe_A',(4.45,-1.5,0),-25)
put('SM_LogStack_A',(6.55,2.8,0),90,.80)
put('SM_Wheelbarrow_A',(5.75,-3.60,0),30)
put('SM_Birdhouse_A',(6.8,-.24,1.36))
put('SM_Signpost_A',(2.35,-5.78,0),-7)
for x in [-4.7,-2.60,.83]:put('SM_StoneWall_A',(x,-5.80,0))
put('SM_Gate_A',(-.90,-5.80,0))
for x in [-1.47,-.32]:
    bowed_beam('Gate_SupportPost',(x,-5.8,0),(x,-5.8,1.15),.14,yard,mat,.012)
    box('Gate_PostCap',(x,-5.8,1.17),(.18,.18,.06),yard,mat,.010)
put('SM_FenceBay_A',(-5.5,.9,0),90)
put('SM_FenceBay_A',(-4.3,3.6,0))
put('SM_FenceBay_A',(-1.7,3.6,0))
put('SM_FenceBay_A',(1.0,3.6,0))
put('SM_FenceBay_A',(7.35,-.6,0),90)
# Sparse ground slabs indicate circulation, not a finished environment/terrain.
for i,(x,y) in enumerate([(.1,-4.0),(-.18,-4.65),(-.58,-5.20)]):
    o=box('Path_Step',(x,y,.025),(.85,.52,.05),yard,mat,.012);o.rotation_euler.z=.08*math.sin(i*2)

# Functional checks on the actual saved hinge hierarchy; restore every pose.
controls=[o for o in bpy.data.objects if o.name.startswith(('CTRL_Door_','CTRL_Shutter_','CTRL_Gate_'))]
hinges=[]
for o in controls:
    bpy.context.view_layer.update();children=[ch for ch in o.children if ch.type=='MESH']
    assert children,o.name
    old=o.rotation_euler.copy();probe=children[0];before=probe.matrix_world.copy()
    o.rotation_euler.z+=.3;bpy.context.view_layer.update();after=probe.matrix_world.copy()
    changed=any(abs(before[i][j]-after[i][j])>1e-6 for i in range(4) for j in range(4))
    o.rotation_euler=old;bpy.context.view_layer.update();assert changed,o.name
    hinges.append({'controller':o.name,'children':len(children),'rotation_moves_child':changed})
report={'house_source':'Source/Openings/v007/House_Cottage_A.blend','yard_source':'Source/Yard/v002/Cottage_Yard_Kit.blend','placements':placements,'distinct_yard_modules':len(set(p['module'] for p in placements)),'hinge_checks':hinges,'limitations':['Demonstration layout, not gameplay navigation or collision validation.','Grey materials; UV/materials/LOD/export remain pending.','Fence segments are placed as samples; this is not a continuous closed enclosure.']}
(ROOT/'QA/courtyard_v008.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
st=bpy.data.collections['90_STUDIO - not exported']
hero=camera('CAM_Courtyard_Hero',(-14,-22,14),(.6,-.9,2.05),18.3,st)
reverse=camera('CAM_Courtyard_Reverse',(17,16,13),(.8,-.5,2.0),18.8,st)
front=camera('CAM_Courtyard_Front',(1,-26,14),(.6,-.8,1.8),18.1,st)
s.camera=hero;s.render.resolution_x=1200;s.render.resolution_y=1200
bpy.ops.object.select_all(action='DESELECT');bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Cottage_Courtyard.blend'))
shutil.copy2(__file__,OUT/Path(__file__).name)
for label,cam in [('01_Hero',hero),('02_Reverse',reverse),('03_Front',front)]:render(s,cam,REND/(label+'.png'),1200)
print('COURTYARD_COMPLETE',len(placements),len(hinges),flush=True)
