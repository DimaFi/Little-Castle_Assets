"""Version 3: continuous stone stair cheeks, restrained vines, optional cottage materials.
Blender --background --factory-startup --python finish_church.py -- --paint
"""
import bpy,bmesh,math,random,json,sys
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parent
ROOT=Path('E:/Games_Develop/CozySettlement')
PAINT='--paint' in sys.argv
bpy.ops.wm.open_mainfile(filepath=str(P.parent/'v002/Church_A.blend'))
S=bpy.context.scene;S.render.threads_mode='FIXED';S.render.threads=8
grey=bpy.data.materials['Clay_Grey_GEOMETRY_ONLY']
stairs=bpy.data.collections['07_ENTRANCE']
vines=bpy.data.collections.new('08_LIGHT_VINES');S.collection.children.link(vines)
def mesh(name,vs,fs,col,mat):
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update()
 ob=bpy.data.objects.new(name,me);col.objects.link(ob);me.materials.append(mat);return ob
def plain(name,color,rough=.8,metal=0):
 m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*color,1)
 p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal;return m
stone=bpy.data.objects['Door_Threshold'].data
for o in list(stairs.objects):
 if o.name.startswith('Step_Cheek'):bpy.data.objects.remove(o,do_unlink=True)
def block(name,pos,dims):
 ob=bpy.data.objects.new(name,stone);stairs.objects.link(ob);ob.location=pos;ob.scale=dims;ob['source_asset']='MOD_StoneWall_A / Wall_Stone';return ob
# Continuous stepped sides: bottom course follows the entire run to the front wall.
segments=[(-5.14,-4.76,.37),(-4.76,-4.38,.51),(-4.38,-4.00,.65),(-4.00,-3.68,.65)]
for sign in [-1,1]:
 for i,(a,b,top) in enumerate(segments):
  block('StairSide_Base',(sign*1.29,(a+b)/2,.121),(.34,b-a-.012,.242))
  bottom=.244
  block('StairSide_Upper',(sign*1.29,(a+b)/2,(bottom+top)/2),(.34,b-a-.012,top-bottom))
# Solid inner backing removes any visible light through joints under treads.
outline=[(-5.14,0),(-3.68,0),(-3.68,.62),(-4.38,.62),(-4.38,.48),(-4.76,.48),(-4.76,.34),(-5.14,.34)]
for sign in [-1,1]:
 k=len(outline);xs=sorted([sign*1.10,sign*1.30])
 vs=[(x,y,z) for x in xs for y,z in outline]
 fs=[tuple(range(k-1,-1,-1)),tuple(range(k,k*2))]+[(i,(i+1)%k,(i+1)%k+k,i+k) for i in range(k)]
 ob=mesh('StairSide_InnerBacking',vs,fs,stairs,grey)
 bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()
# Reuse the existing painted atlas, alpha-tested leaf silhouettes on folded cards.
leaf=plain('M_Church_Vine_ExistingFoliage',(.12,.24,.055),.82)
n=leaf.node_tree.nodes;l=leaf.node_tree.links;p=n.get('Principled BSDF')
tex=n.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(ROOT/'Mat/T_Foliage/T_Foliage_BaseColor.png'),check_existing=True);tex.image.pack();tex.extension='CLIP'
uv=n.new('ShaderNodeUVMap');uv.uv_map='UV0';l.new(uv.outputs[0],tex.inputs[0])
tint=n.new('ShaderNodeMixRGB');tint.blend_type='MULTIPLY';tint.inputs[0].default_value=.60;tint.inputs[2].default_value=(.34,.57,.28,1);l.new(tex.outputs['Color'],tint.inputs[1]);l.new(tint.outputs[0],p.inputs['Base Color'])
alpha=n.new('ShaderNodeMath');alpha.operation='GREATER_THAN';alpha.inputs[1].default_value=.40;l.new(tex.outputs['Alpha'],alpha.inputs[0]);l.new(alpha.outputs[0],p.inputs['Alpha'])
p.inputs['Subsurface Weight'].default_value=.035
leaf.surface_render_method='DITHERED';leaf.use_backface_culling=False
leaf['source']='Existing T_Foliage_BaseColor atlas; isolated lower-row leaves, no new image';leaf['geometry']='4 triangles per folded leaf; intentionally open, two-sided foliage'
stem=plain('M_Church_Vine_Stem',(.105,.12,.035),.91)
patch_reports=[]
def vine_patch(name,origin,right,normal,path,seed,leaf_scale=1):
 rng=random.Random(seed);origin=Vector(origin);right=Vector(right);normal=Vector(normal);up=Vector((0,0,1))
 def xyz(p):return origin+right*p[0]+up*p[1]+normal*p[2]
 sv=[];sf=[];lv=[];lf=[];luv=[]
 def tube(points,r):
  start=len(sv);pts=[xyz(p) for p in points];sides=5
  for i,pt in enumerate(pts):
   d=(pts[min(i+1,len(pts)-1)]-pts[max(i-1,0)]).normalized();a=d.cross(normal).normalized();b=d.cross(a)
   rr=r*(1-.62*i/(len(pts)-1))
   sv.extend([pt+rr*(a*math.cos(j*2*math.pi/sides)+b*math.sin(j*2*math.pi/sides)) for j in range(sides)])
  for i in range(len(pts)-1):
   for j in range(sides):sf.append((start+i*sides+j,start+i*sides+(j+1)%sides,start+(i+1)*sides+(j+1)%sides,start+(i+1)*sides+j))
  sf.extend([tuple(start+j for j in range(sides-1,-1,-1)),tuple(start+(len(pts)-1)*sides+j for j in range(sides))])
 def blade(base,angle,length):
  base=xyz(base);direction=(right*math.sin(angle)+up*math.cos(angle)+normal*rng.uniform(.05,.26)).normalized();across=direction.cross(normal).normalized()
  width=length*.72;start=len(lv)
  # Tip points upward in source crop; mild bend preserves a readable silhouette.
  lv.extend([base-across*width/2,base+across*width/2,base+direction*length+across*width/2,base+direction*length-across*width/2,base+direction*length*.5+normal*.025])
  rect=(422,991,633,1237) if rng.random()<.65 else (911,983,1100,1228)
  x0,y0,x1,y1=rect
  u0,u1=x0/1254,x1/1254;v0,v1=1-y1/1254,1-y0/1254
  luv.extend([(u0,v0),(u1,v0),(u1,v1),(u0,v1),((u0+u1)/2,(v0+v1)/2)])
  lf.extend([(start+i,start+(i+1)%4,start+4) for i in range(4)])
 tube(path,.018)
 for index,(a,b) in enumerate(zip(path,path[1:])):
  a,b=Vector(a),Vector(b);count=max(2,round((b-a).length/.13))
  for j in range(count):
   t=(j+.30)/count;pt=a.lerp(b,t);sign=-1 if (index+j)%2 else 1
   length=rng.uniform(.16,.24)*leaf_scale
   angle=sign*rng.uniform(.48,1.10)
   blade(pt+Vector((sign*.012,0,.02)),angle,length)
  if index>0 and index%2==0:
   pt=a.lerp(b,.4);sign=-1 if index%4==0 else 1
   tip=pt+Vector((sign*.31,.24,.035));middle=pt.lerp(tip,.45)
   tube([pt,middle,tip],.009)
   for j in range(3):blade(pt.lerp(tip,(j+.5)/3)+Vector((0,0,.025)),sign*.85,rng.uniform(.14,.21)*leaf_scale)
 ob=mesh(name+'_Stems',sv,sf,vines,stem)
 ob=mesh(name+'_Leaves',lv,lf,vines,leaf)
 uv=ob.data.uv_layers.new(name='UV0')
 for poly in ob.data.polygons:
  for li in poly.loop_indices:uv.data[li].uv=luv[ob.data.loops[li].vertex_index]
 ob['intentional_open_surface']='Two-sided alpha foliage cards';ob['leaf_count']=len(lv)//5
 patch_reports.append({'patch':name,'leaves':len(lv)//5})
vine_patch('Vine_Left_Pier',(-2.99,-1.16,0),(0,1,0),(-1,0,0),[(0,.18,0),(-.08,.62,.01),(.10,1.04,.025),(-.06,1.51,.04),(.11,1.97,.03),(.04,2.43,.03),(-.09,2.87,.04),(.08,3.36,.02),(-.26,3.55,.02),(-.60,3.62,.03)],31)
vine_patch('Vine_Entrance_Right',(2.22,-3.92,0),(1,0,0),(0,-1,0),[(.08,.14,0),(-.02,.58,.02),(.13,.99,.02),(.02,1.42,.04),(.15,1.82,.01),(.07,2.24,.02),(-.13,2.54,.03)],71,.92)
vine_patch('Vine_Tower_Left',(-1.51,6.54,0),(0,1,0),(-1,0,0),[(0,.12,.0),(-.09,.63,.01),(.07,1.13,.02),(-.08,1.65,.02),(.06,2.14,.02),(-.05,2.66,.02),(.06,3.19,.015),(-.09,3.70,.02),(.04,4.18,.02)],83,.94)
vine_patch('Vine_Right_Pier',(2.99,1.17,0),(0,-1,0),(1,0,0),[(0,.17,0),(.08,.53,.02),(-.06,.92,.02),(.08,1.34,.03),(-.04,1.76,.03)],97,.90)
if PAINT:
 source=ROOT/'Art/House_Cottage_A/Source/Roof/v018/House_Cottage_A.blend'
 names=['M_Cottage_WarmPlaster_A','M_Cottage_Terracotta_A','M_Cottage_StructuralTimber_A','M_Cottage_FieldStone_A','M_Cottage_FrameWood_A','M_Cottage_DoorWood_A','M_Cottage_ForgedIron_A','M_Cottage_WindowGlass_Proxy_A','M_Cottage_RoofUnderlay_A']
 with bpy.data.libraries.load(str(source),link=False) as (a,b):b.materials=names
 mats=dict(zip(['plaster','roof','timber','stone','frame','door','iron','glass','underlay'],b.materials))
 mats['bronze']=plain('M_Church_Bell_Bronze',(.30,.185,.065),.36,.72)
 # Keep the cottage palette; all packed original maps remain embedded.
 def role(o):
  n=o.name
  if n.startswith('Bell_Hollow'):return 'bronze'
  if n.startswith(('Bell_Clapper','Bell_Hanger','Clapper_Head')) or any(t in n for t in ['Hinge','Rivet','_Ring']):return 'iron'
  if 'DoorPlank' in n or n.startswith('Entrance_Inset'):return 'door'
  if 'MOD_StoneWall_A' in o.get('source_asset',''):return 'stone'
  if '_Inset' in n:return 'glass'
  if any(t in n for t in ['_Tracery','_Mullion','_Frame']):return 'frame'
  if 'Substrate' in n:return 'underlay'
  if ('Tile' in n or 'Ridge' in n) and 'Cross' not in n:return 'roof'
  if o.data.name.startswith('Cottage_Beam') or any(t in n for t in ['_Post','_Tie','_Brace','_Verge','_Eave','_Bracket','KingPost','Bell_Yoke']):return 'timber'
  if n in ['Nave_Front','Nave_Rear','Tower_Shaft_Centred','Belfry_Continuous_Masonry','Rear_Connection_Walls','Porch_Gable'] or n.startswith('Nave_Side'):return 'plaster'
  return 'stone'
 # Data stays shared for repeat modules with the same material role.
 cache={}
 for o in list(S.objects):
  if o.type!='MESH' or o.name in vines.objects or any(c.name=='90_STUDIO' for c in o.users_collection):continue
  r=role(o);key=(o.data.name,r)
  if key not in cache:
   data=o.data.copy();data.materials.clear();data.materials.append(mats[r]);uv=data.uv_layers.get('UV0') or data.uv_layers.new(name='UV0')
   lo=Vector([min(v.co[i] for v in data.vertices) for i in range(3)]);hi=Vector([max(v.co[i] for v in data.vertices) for i in range(3)])
   for f in data.polygons:
    f.material_index=0;drop=max(range(3),key=lambda i:abs(f.normal[i]));axes=[i for i in range(3) if i!=drop]
    for li in f.loop_indices:
     p=data.vertices[data.loops[li].vertex_index].co
     a,b=axes
     if r=='plaster':q=(p[a]*.43+.17,p[b]*.43+.11)
     elif r=='door':
      across=0 if drop!=0 else 1
      strip=[.025,.17,.35,.52,.70,.88][sum(map(ord,o.name))%6]
      q=(strip+(p[across]-lo[across])/max(hi[across]-lo[across],.001)*.055,.06+(p.z-lo.z)*.39)
     elif r in ['timber','frame']:
      long=2 if r!='frame' else max(range(3),key=lambda i:hi[i]-lo[i]);cross=next(i for i in axes if i!=long) if long in axes else axes[0]
      q=(.12+(p[long]-lo[long])/max(hi[long]-lo[long],.001)*.73,.2+(p[cross]-lo[cross])/max(hi[cross]-lo[cross],.001)*.21) if long in axes else (.12+p[a]*.3,.2+p[b]*.3)
     elif r=='stone':q=(.223+(p[a]-(lo[a]+hi[a])/2)/max(hi[a]-lo[a],.001)*.084,.689+(p[b]-(lo[b]+hi[b])/2)/max(hi[b]-lo[b],.001)*.056)
     else:q=(.32+(p[a]-lo[a])/max(hi[a]-lo[a],.001)*.22,.29+(p[b]-lo[b])/max(hi[b]-lo[b],.001)*.24)
     uv.data[li].uv=q
   cache[key]=data
  o.data=cache[key];o['material_role']=r
S.camera=bpy.data.objects['CAM_01_Front_Left'];S['asset_stage']='Church_A v003: closed stair cheeks and light vines'+(' / cottage materials' if PAINT else ' / grey architecture')
S.cycles.samples=32;S.cycles.transparent_max_bounces=16
S.render.resolution_x=1200;S.render.resolution_y=1200
bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();total=0;vine_tri=0;issues=[]
for o in S.objects:
 if o.type!='MESH' or any(c.name=='90_STUDIO' for c in o.users_collection):continue
 ev=o.evaluated_get(deps);me=ev.to_mesh();me.calc_loop_triangles();num=len(me.loop_triangles);total+=num
 if o.name in vines.objects:vine_tri+=num
 if any(t.area<1e-10 for t in me.loop_triangles):issues.append(o.name)
 ev.to_mesh_clear()
report={'version':'v003','painted_architecture':PAINT,'triangles_total':total,'previous_triangles':49196,'added_triangles_net':total-49196,'vine_triangles':vine_tri,'patches':patch_reports,'degenerate_objects':issues,'leaf_texture':'CozySettlement/Mat/T_Foliage/T_Foliage_BaseColor.png','stair_side_cladding':'16 source stone blocks plus 2 closed backing meshes','engine_ready':False}
(P/'geometry_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');assert not issues,issues
bpy.ops.wm.save_as_mainfile(filepath=str(P/'Church_A.blend'))
print('REPORT',json.dumps(report),flush=True)
for cam,name in [('CAM_01_Front_Left','01_Hero'),('CAM_04_Entrance','02_Entrance'),('CAM_02_Rear_Right','03_Rear')]:
 S.camera=bpy.data.objects[cam];S.render.filepath=str(P/(name+'.png'));bpy.ops.render.render(write_still=True)
print('FINISHED',flush=True)
