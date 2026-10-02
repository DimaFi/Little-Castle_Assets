"""Standalone door/window variants, plus read-back validation of saved yard files."""
import sys,json,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from kit_geometry import *
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'Source/Modules/Openings_v002';REND=ROOT/'Renders/Openings/v002'
OUT.mkdir(parents=True,exist_ok=True);REND.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Source/Openings/v007/House_Cottage_A.blend'))
mat=bpy.data.materials['M_Blockout_Grey'];world=bpy.context.scene.world
specs=[('SM_Door_Entrance_A',list(bpy.data.collections['08_DOORS'].all_objects),(.8,-2.40,.39)),
       ('SM_Window_Open_A',[o for o in bpy.data.collections['07_WINDOWS'].all_objects if 'Front_L' in o.name],(-1.56,-2.43,.975)),
       ('SM_Window_Small_A',[o for o in bpy.data.collections['07_WINDOWS'].all_objects if 'Front_R' in o.name],(2.37,-2.43,1.295)),
       ('SM_Window_Closed_A',[o for o in bpy.data.collections['07_WINDOWS'].all_objects if 'Front_L' in o.name and 'Shutter' not in o.name],(-1.56,-2.43,.975))]
records=[]
for name,objects,offset in specs:
    target=OUT/name/(name+'.blend')
    if target.exists():raise FileExistsError(target)
    target.parent.mkdir(parents=True,exist_ok=True)
    sc=bpy.data.scenes.new(name);sc.world=world;sc.unit_settings.system='METRIC';sc.unit_settings.scale_length=1
    sc.render.engine='CYCLES';sc.cycles.samples=20;sc.cycles.use_denoising=True;sc.render.threads_mode='FIXED';sc.render.threads=8
    sc.view_settings.view_transform='AgX';bpy.context.window.scene=sc
    c=collection(name);shift=Matrix.Translation(-Vector(offset));mapping={}
    for o in objects:
        n=o.copy()
        if o.type=='MESH':n.data=o.data.copy()
        c.objects.link(n);mapping[o]=n
    def depth(o):
        n=0
        while o.parent is not None:n+=1;o=o.parent
        return n
    # Parent transforms must be finalized BEFORE assigning a child's world pose.
    for o,n in sorted(mapping.items(),key=lambda pair:depth(pair[0])):
        n.parent=mapping.get(o.parent);n.matrix_world=shift@o.matrix_world
        bpy.context.view_layer.update()
    if name=='SM_Window_Closed_A':
        width=.79;bottom=.055;spring=bottom+1.02-width/2
        for side in [-1,1]:
            root=root_empty('CTRL_ClosedShutter_'+('L' if side<0 else 'R'),c,(side*width/2,-.115,bottom));pieces=[]
            for i in range(3):
                a=(-width/2 if side<0 else 0)+i*width/6+.0025;b=a+width/6-.005
                top=[(b+(a-b)*j/5,spring+math.sqrt(max(0,(width/2)**2-(b+(a-b)*j/5)**2))) for j in range(6)]
                pieces.append(prism('Closed_Shutter_Plank',[(a,bottom),(b,bottom)]+top,-.155,-.075,c,mat,.007))
            for z in [.25,.68]:pieces.append(box('Closed_Shutter_CrossBrace',(side*width/4,-.18,z),(.35,.04,.057),c,mat,.009))
            parent_world(pieces,root)
    st=studio(sc,mat);ground=next(o for o in st.objects if o.name.startswith('Studio ground'));ground.location.z=-.125
    lo,hi=bounds(list(c.all_objects));center=Vector([(lo[i]+hi[i])/2 for i in range(3)]);dim=max(hi[i]-lo[i] for i in range(3))
    cam=camera('CAM_'+name,center+Vector((2.3,-7,2.3)),center,dim*1.42,st);sc.camera=cam
    stats=inspect_geometry(list(c.all_objects));assert not stats['issues'],stats
    stats.update({'name':name,'file':str(target.relative_to(ROOT))});records.append(stats)
    bpy.data.libraries.write(str(target),{sc},fake_user=True)
    render(sc,cam,REND/(name+'.png'),600)

# Reopen the actual files, not just their generating collections.
yard=json.loads((ROOT/'QA/yard_v002.json').read_text(encoding='utf-8'))
saved=[]
files=[(m['name'],ROOT/'Source/Yard/v002/Modules'/m['name']/(m['name']+'.blend')) for m in yard['modules']]
files += [(r['name'],ROOT/r['file']) for r in records]
for name,file in files:
    bpy.ops.wm.open_mainfile(filepath=str(file));sc=bpy.data.scenes[name];c=bpy.data.collections[name]
    bpy.context.window.scene=sc;stats=inspect_geometry(list(c.all_objects))
    assert not stats['issues'],(name,stats)
    assert sc.camera is not None,name
    assert abs(sc.unit_settings.scale_length-1)<1e-8,name
    saved.append({'name':name,'file':str(file.relative_to(ROOT)),'geometry_clean':True,'camera_saved':True,'metres':True,'objects':stats['objects'],'triangles':stats['triangles']})
(ROOT/'QA/module_readback.json').write_text(json.dumps({'passed':True,'files_checked':len(saved),'modules':saved},indent=2),encoding='utf-8')
(ROOT/'QA/opening_modules.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
print('READBACK_VALIDATION_COMPLETE',len(saved),flush=True)
