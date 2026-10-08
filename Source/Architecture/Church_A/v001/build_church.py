"""Church geometry checkpoint. Blender 4.4, metres, front -Y, rear tower +Y.
Reuses Cottage_A stone / timber / tile / ridge meshes; no final materials.
Run --background --factory-startup --python build_church.py
"""
import bpy, bmesh, math, json
from pathlib import Path
from mathutils import Vector, Matrix
O=Path(__file__).resolve().parent
SRC=Path('E:/Games_Develop/CozySettlement/Art/House_Cottage_A')
bpy.ops.wm.read_factory_settings(use_empty=True)
S=bpy.context.scene
S.unit_settings.system='METRIC'
def col(n):
 c=bpy.data.collections.new(n);S.collection.children.link(c);return c
C=col('01_NAVE'); F=col('02_FOUNDATION_AND_MASONRY'); T=col('03_TIMBER'); R=col('04_TILED_ROOFS'); W=col('05_WINDOWS_AND_DOOR'); B=col('06_REAR_BELL_TOWER'); P=col('07_ENTRANCE'); L=col('90_STUDIO')
M=bpy.data.materials.new('Clay_Grey_GEOMETRY_ONLY');M.diffuse_color=(.52,.52,.52,1);M.use_nodes=True
M.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.52,.52,.52,1)
M.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.8
def mesh(n,v,f,c,bevel=0):
 me=bpy.data.meshes.new(n);me.from_pydata(v,[],f);me.update()
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
 ob=bpy.data.objects.new(n,me);c.objects.link(ob);me.materials.append(M)
 if bevel:
  m=ob.modifiers.new('One segment softened edges','BEVEL');m.width=bevel;m.segments=1
  m=ob.modifiers.new('Weighted normals','WEIGHTED_NORMAL');m.keep_sharp=True
 return ob
def box(n,p,d,c,bevel=.025):
 x,y,z=[a/2 for a in d]
 ob=mesh(n,[(-x,-y,-z),(-x,-y,z),(-x,y,-z),(-x,y,z),(x,-y,-z),(x,-y,z),(x,y,-z),(x,y,z)],[(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)],c,bevel);ob.location=p;return ob
def prism(n,outline,y0,y1,c,bevel=.015):
 k=len(outline)
 return mesh(n,[(x,y,z) for y in [y0,y1] for x,z in outline],[tuple(range(k-1,-1,-1)),tuple(range(k,2*k))]+[(i,(i+1)%k,(i+1)%k+k,i+k) for i in range(k)],c,bevel)
def bake(ob):
 bpy.context.view_layer.objects.active=ob;ob.select_set(True)
 for m in list(ob.modifiers):bpy.ops.object.modifier_apply(modifier=m.name)
 ob.select_set(False)
def load(path,names):
 with bpy.data.libraries.load(str(path),link=False) as (a,b):b.objects=names
 for ob in b.objects:
  C.objects.link(ob);ob.hide_viewport=False;ob.hide_render=False;ob.hide_set(False)
 return b.objects
stone,wood=load(SRC/'Source/Modules/v002/Cottage_A_Primitives.blend',['SM_Foundation_Block_A','SM_Beam_Vertical_A'])
tile,cap=load(SRC/'Source/Openings/v007/House_Cottage_A.blend',['SM_RoofTile_Shared_0','SM_Roof_RidgeCap_Shared_A'])
# Keep end/middle rings of the cottage beam: bow survives, redundant rings go.
wv=[tuple(wood.data.vertices[i].co) for i in list(range(4))+list(range(8,12))+list(range(16,20))]
wf=[(3,2,1,0),(8,9,10,11)]+[(r*4+j,r*4+(j+1)%4,(r+1)*4+(j+1)%4,(r+1)*4+j) for r in range(2) for j in range(4)]
wm=bpy.data.meshes.new('Cottage_Beam_Reduced');wm.from_pydata(wv,[],wf);wm.update();wood.data=wm
for ob in [stone,wood]:
 for mod in ob.modifiers:
  if mod.type=='BEVEL':mod.segments=1
 bake(ob)
 # Normalized source mesh; all installed instances share these data blocks.
 lo=Vector([min(v.co[i] for v in ob.data.vertices) for i in range(3)])
 hi=Vector([max(v.co[i] for v in ob.data.vertices) for i in range(3)])
 for v in ob.data.vertices:
  for i in range(3):v.co[i]=(v.co[i]-(lo[i]+hi[i])/2)/(hi[i]-lo[i])
 ob.data.materials.clear();ob.data.materials.append(M)
stone_data=stone.data;wood_data=wood.data
tile_samples=[tuple(tile.data.vertices[i].co) for i in [0,2,4,15,17,19]]
cap_data=cap.data.copy();cap_data.materials.clear();cap_data.materials.append(M)
for ob in [stone,wood,tile,cap]:bpy.data.objects.remove(ob,do_unlink=True)
def inst(n,data,p,scale,c):
 ob=bpy.data.objects.new(n,data);c.objects.link(ob);ob.location=p;ob.scale=scale
 ob['source_asset']='House_Cottage_A';return ob
def block(n,p,d,c=F):return inst(n,stone_data,p,d,c)
def beam(n,a,b,w=.18,c=T,depth=None):
 a,b=Vector(a),Vector(b);d=b-a
 ob=inst(n,wood_data,(a+b)/2,(w,depth or w,d.length),c);ob.rotation_euler=d.to_track_quat('Z','Y').to_euler();return ob
def tube(n,pts,r,c=W,sides=6):
 vs=[];fs=[];pts=[Vector(p) for p in pts]
 for i,p in enumerate(pts):
  tangent=(pts[min(i+1,len(pts)-1)]-pts[max(i-1,0)]).normalized()
  u=tangent.cross(Vector((0,1,0)))
  if u.length<.01:u=tangent.cross(Vector((1,0,0)))
  u.normalize();v=tangent.cross(u)
  vs += [p+r*(u*math.cos(j*2*math.pi/sides)+v*math.sin(j*2*math.pi/sides)) for j in range(sides)]
 for i in range(len(pts)-1):
  for j in range(sides):fs.append((i*sides+j,i*sides+(j+1)%sides,(i+1)*sides+(j+1)%sides,(i+1)*sides+j))
 fs += [tuple(range(sides-1,-1,-1)),tuple(range(len(vs)-sides,len(vs)))]
 return mesh(n,vs,fs,c)
def cut(ob,cutter):
 bpy.context.view_layer.objects.active=ob
 m=ob.modifiers.new('True recessed opening','BOOLEAN');m.object=cutter;m.operation='DIFFERENCE';m.solver='EXACT'
 # Boolean before edge bevel.
 bpy.ops.object.modifier_move_to_index(modifier=m.name,index=0)
 bpy.ops.object.modifier_apply(modifier=m.name);bpy.data.objects.remove(cutter,do_unlink=True)
def gothic(w,base,h,n=4):
 r=w/2;spring=base+h-math.sqrt(3)*r
 # Right spring to apex, then left spring, two circular arcs.
 arc=[(-r+w*math.cos(math.pi/3*i/n),spring+w*math.sin(math.pi/3*i/n)) for i in range(n+1)]
 arc += [(r+w*math.cos(2*math.pi/3+math.pi/3*i/n),spring+w*math.sin(2*math.pi/3+math.pi/3*i/n)) for i in range(1,n+1)]
 return [(-r,base),(r,base)]+arc
def place(ob,origin,angle):
 ob.location=origin;ob.rotation_euler.z=angle;return ob
def opening(n,wall,origin,angle,w,base,h,door=False,tracery=True):
 outline=gothic(w,base,h)
 cutter=prism(n+'_cut',outline,-.5,.5,W,0);place(cutter,origin,angle);cut(wall,cutter)
 inset=prism(n+'_Inset',outline,.11,.16,W,.006);place(inset,origin,angle)
 created=[];spring=base+h-math.sqrt(3)*w/2
 # Segmented stone surround: straight jambs then paired pointed arches.
 count=max(2,round((spring-base)/.32));step=(spring-base)/count
 for sign in [-1,1]:
  for i in range(count):created.append(block(n+'_Jamb',(sign*(w/2+.115),-.07,base+(i+.5)*step),(.23,.27,step-.014),W))
 inner=outline[2:];outer=gothic(w+.46,base,h+.40)[2:]
 for i in range(len(inner)-1):
  a,b=Vector(inner[i]),Vector(inner[i+1]);c,d=Vector(outer[i]),Vector(outer[i+1]);gap=.025
  a,b=a.lerp(b,gap),a.lerp(b,1-gap);c,d=c.lerp(d,gap),c.lerp(d,1-gap)
  created.append(prism(n+'_ArchStone',[a,b,d,c],-.215,.075,W,.018))
 if not door:
  created.append(block(n+'_Sill',(0,-.105,base-.08),(w+.58,.40,.18),W))
  # Thin wood frame slightly in front of the inset, with pointed twin lights.
  created.append(tube(n+'_Frame',[(x,.045,z) for x,z in outline+[outline[0]]],.043))
  created.append(beam(n+'_Mullion',(0,.015,base+.02),(0,.015,base+h-.18),.067,W))
  if tracery:
   for sign in [-1,1]:
    pts=[(sign*w*.40,.015,base+h*.42),(sign*w*.27,.015,base+h*.59),(0,.015,base+h*.73)]
    created.append(tube(n+'_Tracery',pts,.034))
 else:
  # Individual door planks fitted below pointed arch.
  def top(x):return spring+math.sqrt(max(0,w*w-(abs(x)+w/2)**2))
  for i in range(8):
   a=-w/2+i*w/8+.012;b=-w/2+(i+1)*w/8-.012
   created.append(prism(n+'_DoorPlank',[(a,base+.025),(b,base+.025),(b,top(b)-.025),(a,top(a)-.025)],-.015,.095,W,.008))
  for sign in [-1,1]:
   for z in [base+.48,base+1.34]:
    created.append(box(n+'_Hinge',(sign*w*.26,-.065,z),(w*.40,.06,.075),W,.012))
    for x in [sign*w*.1,sign*w*.41]:created.append(block(n+'_HingeRivet',(x,-.107,z),(.043,.04,.043),W))
   pts=[(sign*.15+.088*math.cos(j*2*math.pi/12),-.13,base+.92+.11*math.sin(j*2*math.pi/12)) for j in range(13)]
   created.append(tube(n+'_Ring',pts,.022))
 for ob in created:
  ob.location=Vector(origin)+Matrix.Rotation(angle,3,'Z')@ob.location;ob.rotation_euler.z+=angle
 return inset
# Main body: separate walls allow later modular reuse.
front=prism('Nave_Front',[(-2.8,.38),(2.8,.38),(2.8,4.13),(0,6.63),(-2.8,4.13)],-3.7,-3.42,C)
rear=prism('Nave_Rear',[(-2.8,.38),(2.8,.38),(2.8,4.13),(0,6.63),(-2.8,4.13)],3.42,3.7,C)
walls=[]
for sign in [-1,1]:
 wall=box('Nave_Side_'+str(sign),(sign*2.66,0,2.27),(.28,7.4,3.78),C);walls.append(wall)
 for y in [-2.35,0,2.35]:opening('SideWindow',wall,(sign*2.81,y,0),sign*math.pi/2,1.0,1.08,2.16)
 for y in [-3.59,-1.18,1.18,3.59]:
  beam('Nave_Post',(sign*2.85,y,.40),(sign*2.85,y,4.15),.21)
  for dy in [-.66,.66]:
   if abs(y+dy)<3.7:beam('Nave_Brace',(sign*2.86,y,3.40),(sign*2.86,y+dy,4.05),.135)
 beam('Nave_Eave_Beam',(sign*2.84,-3.85,4.02),(sign*2.84,3.85,4.02),.24)
opening('Entrance',front,(0,-3.71,0),0,1.63,.47,2.28,True)
opening('Front_Gothic_Window',front,(0,-3.71,0),0,1.43,3.55,1.95)
for x in [-2.64,2.64]:beam('Front_Post',(x,-3.77,.46),(x,-3.77,4.22),.22)
for sign in [-1,1]:beam('Front_Gable_Tie',(sign*1.04,-3.8,4.12),(sign*2.7,-3.8,4.12),.21)
beam('Front_KingPost',(0,-3.78,5.74),(0,-3.78,6.61),.20)
# Foundation bond and corner stones.
for row in range(2):
 z=.145+row*.285
 for sign in [-1,1]:
  for i in range(13):block('Nave_Foundation_Side',(sign*2.78,-3.42+i*.57,z),(.39,.55,.27))
  for i in range(10):
   x=-2.54+i*.565
   if sign<0 and abs(x)<1.06:continue
   block('Nave_Foundation_End',(x,sign*3.66,z),(.545,.40,.27))
 for x in [-2.76,2.76]:
  for y in [-3.65,3.65]:block('Nave_Corner_Base',(x,y,.64+row*.32),(.48,.49,.31))
# Roof surfaces retain the old tile width curvature and lip in closed 20-triangle meshes.
tile_cache={}
def tiledata(width,length):
 key=(round(width,4),round(length,4))
 if key in tile_cache:return tile_cache[key]
 vs=[(x/.32*width,y/.52*length,z) for x,y,z in tile_samples]
 vs += [(x,y,z-.033) for x,y,z in vs]
 fs=[]
 for j in range(1):
  for i in range(2):
   k=j*3+i;fs += [(k,k+1,k+4,k+3),(k+6,k+9,k+10,k+7)]
 border=[0,1,2,5,4,3]
 fs += [(a,b,b+6,a+6) for a,b in zip(border,border[1:]+border[:1])]
 ob=mesh('Cottage_Tile_Reduced',vs,fs,R);data=ob.data;bpy.data.objects.remove(ob,do_unlink=True);tile_cache[key]=data;return data
def capinst(n,p,scale=(1,1,1),rot=math.pi/2):
 ob=inst(n,cap_data,p,scale,R);ob.rotation_euler.z=rot
 # Source cap is open; add thickness without bevel inflation.
 m=ob.modifiers.new('Cap thickness','SOLIDIFY');m.thickness=.035;return ob
def gable_roof(n,half,y0,y1,peak,drop,rows,cols):
 def height(x):
  t=abs(x)/half;return peak-drop*(1.23*t-.23*t*t)
 for sign in [-1,1]:
  outline=[(sign*half*i/8,height(half*i/8)) for i in range(9)]
  outline += [(x,z-.12) for x,z in reversed(outline)]
  prism(n+'_Substrate',outline,y0,y1,R,.01)
  for row in range(rows):
   outer=half*(1-row/rows);inner=max(.012,outer-half/rows*1.23)
   x=sign*outer;xi=sign*inner;z=height(x);zi=height(xi)
   length=math.hypot(xi-x,zi-z)
   up=Vector((xi-x,0,zi-z)).normalized();across=Vector((0,sign,0));normal=across.cross(up)
   step=(y1-y0)/cols
   boundaries=[y0]+[y0+(i+(.5 if row%2 else 1))*step for i in range(cols) if y0+(i+(.5 if row%2 else 1))*step<y1-.03]+[y1]
   for a,b in zip(boundaries,boundaries[1:]):
    data=tiledata(b-a-.013,length)
    ob=inst(n+'_Tile',data,(x,(a+b)/2,z+.053),(1,1,1),R);ob.rotation_euler=Matrix((across,up,normal)).transposed().to_euler()
  beam(n+'_Eave',(sign*half,y0-.035,height(half)-.045),(sign*half,y1+.035,height(half)-.045),.20)
  for y in [y0-.025,y1+.025]:
   for i in range(4):
    a=half*i/4;b=half*(i+1)/4
    beam(n+'_Verge',(sign*a,y,height(a)+.005),(sign*b,y,height(b)+.005),.20)
 for i in range(math.ceil((y1-y0)/.40)):
  y=y0+.19+i*.40
  capinst(n+'_Ridge',(0,y,peak+.06),(.98,.88,.88))
 return height
gable_roof('Nave_Roof',3.12,-3.96,3.94,6.71,2.64,10,17)
# Small centred porch; ends well inside the facade corners.
for x in [-1.17,1.17]:
 beam('Porch_Post',(x,-4.30,.45),(x,-4.30,2.88),.16,P)
 beam('Porch_Bracket',(x,-4.30,2.37),(x,-3.83,2.84),.13,P)
gable_roof('Porch_Roof',1.40,-4.59,-3.65,3.61,.87,4,3)
prism('Porch_Gable',[(-1.18,2.77),(1.18,2.77),(0,3.56)],-4.32,-4.20,P)
beam('Porch_Tie',(-1.23,-4.39,2.81),(1.23,-4.39,2.81),.16,P)
for i in range(3):block('Entrance_Step',(0,-4.76+i*.24,.08+i*.145),(2.45-i*.12,.94-i*.14,.16),P)
for sign in [-1,1]:
 for i in range(3):block('Step_Cheek',(sign*1.28,-4.85+i*.34,.20+i*.14),(.30,.34,.37),P)
# Rear tower: exact x=0 centre, a rectangular shaft behind the rear wall.
TY=5.02;TW=1.35
shaft=box('Tower_Shaft_Centred',(0,TY,3.50),(2.70,2.70,6.40),B,.035)
shaft['rear_alignment']='x = 0; footprint y = 3.67 .. 6.37, behind nave'
for sign in [-1,1]:
 opening('Tower_Lancet',shaft,(sign*1.36,TY,0),sign*math.pi/2,.56,3.55,1.63,tracery=False)
opening('Tower_Rear_Lancet',shaft,(0,TY+1.36,0),math.pi,.56,3.55,1.63,tracery=False)
for row in range(21):
 z=.17+row*.31
 for x in [-1.31,1.31]:
  for y in [TY-1.31,TY+1.31]:
   d=(.49,.37,.294) if row%2 else (.37,.49,.294)
   block('Tower_Quoin',(x,y,z),d,B)
for z in [.16,.45,6.43,8.88]:
 for sign in [-1,1]:
  for i in range(5):
   block('Tower_Belt',(sign*1.36,TY-1.08+i*.54,z),(.42,.525,.26),B)
   block('Tower_Belt',(-1.08+i*.54,TY+sign*1.36,z),(.525,.42,.26),B)
# Belfry has four true pointed open arches, no glass or backing planes.
for angle in [0,math.pi/2,math.pi,3*math.pi/2]:
 origin=Vector((0,TY,0))+Matrix.Rotation(angle,3,'Z')@Vector((0,-1.20,0))
 ob=box('Belfry_Arch_Wall',(0,0,7.72),(2.7,.30,2.40),B,.02)
 # bake box's centre into vertices for consistent local mounting transform
 for v in ob.data.vertices:v.co.z+=7.72
 ob.location=(0,0,0);place(ob,origin,angle)
 cutter=prism('Belfry_Opening_Cut',gothic(1.55,6.68,1.93),-.6,.6,B,0);place(cutter,origin,angle);cut(ob,cutter)
 # Ring voussoirs keep the same proportions as nave windows.
 inner=gothic(1.55,6.68,1.93)[2:];outer=gothic(1.99,6.68,2.31)[2:]
 for i in range(len(inner)-1):
  a,b=Vector(inner[i]),Vector(inner[i+1]);c,d=Vector(outer[i]),Vector(outer[i+1]);u=a.lerp(b,.025);v=a.lerp(b,.975);q=c.lerp(d,.975);p=c.lerp(d,.025)
  o=prism('Belfry_ArchStone',[u,v,q,p],-.215,.05,B,.018);place(o,origin,angle)
for x in [-1.26,1.26]:
 for y in [TY-1.26,TY+1.26]:
  for row in range(7):block('Belfry_Corner_Stone',(x,y,6.65+row*.31),(.39,.39,.295),B)
box('Belfry_Floor',(0,TY,6.50),(2.85,2.85,.17),B)
box('Belfry_Ceiling',(0,TY,8.96),(2.95,2.95,.20),B)
beam('Bell_Yoke',(-1.19,TY,8.31),(1.19,TY,8.31),.21,B)
tube('Bell_Hanger',[(0,TY,7.89),(0,TY,8.32)],.055,B,10)
# Low-sided hollow bell, rolled lip, inside wall and clapper.
profile=[(.12,8.02),(.24,7.94),(.29,7.78),(.31,7.50),(.40,7.23),(.56,7.10),(.57,7.02),(.49,7.00),(.40,7.10),(.28,7.39),(.23,7.72),(.17,7.83),(.10,7.85)]
vs=[(r*math.cos(i*2*math.pi/20),TY+r*math.sin(i*2*math.pi/20),z) for r,z in profile for i in range(20)]
fs=[(j*20+i,j*20+(i+1)%20,((j+1)%len(profile))*20+(i+1)%20,((j+1)%len(profile))*20+i) for j in range(len(profile)) for i in range(20)]
bell=mesh('Bell_Hollow_20_Sides',vs,fs,B)
for p in bell.data.polygons:p.use_smooth=True
tube('Bell_Clapper',[(0,TY,7.68),(0,TY,6.95)],.062,B,10)
block('Clapper_Head',(0,TY,6.98),(.17,.17,.18),B)
# Flared pyramidal tower roof, 7 stepped tile courses per face.
def hz(t):return 9.12+2.08*(1-t)**1.32
for side in range(4):
 angle=side*math.pi/2;rot=Matrix.Rotation(angle,3,'Z')
 def hp(u,t):return Vector((0,TY,0))+rot@Vector((u*1.76*t,-1.76*t,hz(t)))
 # roof backing is a closed wedge following curved profile
 vs=[hp(u,t) for t in [1-i/8 for i in range(8)]+[.018] for u in [-1,1]]
 fs=[(2*i,2*i+1,2*i+3,2*i+2) for i in range(8)]
 ob=mesh('Tower_Hip_Substrate',vs,fs,R);m=ob.modifiers.new('Roof backing thickness','SOLIDIFY');m.thickness=.10
 for row in range(7):
  t=1-row/7;top=max(.018,t-1.23/7);num=max(2,round(9*t))
  for i in range(num):
   v=[]
   for x,y,z in tile_samples:
    f=y/.52;tt=t+(top-t)*f;u=-1+2*(i+.025+(x/.32+.5)*.95)/num
    p=hp(u,tt);p.z+=z+.055;v.append(p)
   v += [p-Vector((0,0,.032)) for p in v]
   faces=[]
   for j in range(1):
    for k in range(2):
     q=j*3+k;faces += [(q,q+1,q+4,q+3),(q+6,q+9,q+10,q+7)]
   border=[0,1,2,5,4,3]
   faces += [(a,b,b+6,a+6) for a,b in zip(border,border[1:]+border[:1])]
   ob=mesh('Tower_Hip_Cottage_Tile',v,faces,R);ob['source_asset']='Cottage tile 3x2 resample, tapered to hip'
 beam('Tower_Eave',hp(-1,1)-Vector((0,0,.07)),hp(1,1)-Vector((0,0,.07)),.20)
 # Thick tapered hip ridges made from the cottage timber form in grey stage.
 for i in range(7):beam('Tower_Hip_Ridge',hp(-1,1-i/7)+Vector((0,0,.09)),hp(-1,max(.018,1-(i+1)/7))+Vector((0,0,.09)),.15,R)
for x in [-1.2,1.2]:
 for sign in [-1,1]:beam('Tower_Eave_Bracket',(x,TY+sign*1.23,8.51),(x,TY+sign*1.62,9.02),.14,B)
def cross(n,x,y,z,size,c):
 block(n+'_Foot',(x,y,z),(.43*size,.40*size,.32*size),c)
 block(n+'_Vertical',(x,y,z+.61*size),(.19*size,.19*size,1.0*size),c)
 block(n+'_Arms',(x,y,z+.76*size),(.70*size,.19*size,.18*size),c)
cross('Tower_Cross',0,TY,11.21,1,B)
cross('Front_Cross',0,-3.87,6.82,.78,T)
# Validation counts evaluated, installed geometry, never unique mesh counts alone.
# Bake only unique architectural walls and clean numerical boolean slivers.
for ob in [front,rear]+walls+[shaft]+[o for o in B.objects if o.name.startswith('Belfry_Arch_Wall')]:
 bake(ob)
 bm=bmesh.new();bm.from_mesh(ob.data)
 bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00001)
 bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=.00001)
 bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free();ob.data.update()
bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();issues=[];total=0;by_collection={}
for c in [C,F,T,R,W,B,P]:
 count=0
 for ob in c.objects:
  if ob.type!='MESH':continue
  ev=ob.evaluated_get(deps);me=ev.to_mesh();me.calc_loop_triangles();count+=len(me.loop_triangles)
  if any(t.area<1e-10 for t in me.loop_triangles):issues.append(ob.name+': degenerate triangles')
  if any(not all(math.isfinite(a) for a in v.co) for v in me.vertices):issues.append(ob.name+': nonfinite')
  ev.to_mesh_clear()
 by_collection[c.name]=count;total+=count
report={'stage':'Unpainted geometry checkpoint; no UV, textures, LODs or engine release','triangles_evaluated':total,'triangles_by_collection':by_collection,'issues':issues,'tower_center_x':0,'tower_center_y':TY,'tower_height_m':12.32,'nave_roof_peak_m':6.71,'source_files':[str(SRC/'Source/Modules/v002/Cottage_A_Primitives.blend'),str(SRC/'Source/Openings/v007/House_Cottage_A.blend')],'reuse':'Source stone, timber, ridge; reduced source tile profile. Gothic openings and bell authored for church.'}
(O/'geometry_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('GEOMETRY_REPORT',json.dumps(report),flush=True)
# Neutral studio and saved cameras.
box('Studio_Ground',(0,0,-.16),(200,200,.26),L,0)
S.world=bpy.data.worlds.new('Neutral Studio');S.world.use_nodes=True
S.world.node_tree.nodes['Background'].inputs[0].default_value=(.32,.32,.32,1);S.world.node_tree.nodes['Background'].inputs[1].default_value=.55
for name,pos,power,size in [('Key',(-8,-10,16),2900,8),('Fill',(8,-4,10),1700,7),('Rim',(1,11,15),3400,6)]:
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;ob=bpy.data.objects.new(name,d);L.objects.link(ob);ob.location=pos;ob.rotation_euler=(Vector((0,1,5))-ob.location).to_track_quat('-Z','Y').to_euler()
def camera(n,pos,target,scale):
 d=bpy.data.cameras.new(n);d.type='ORTHO';d.ortho_scale=scale;ob=bpy.data.objects.new(n,d);L.objects.link(ob);ob.location=pos;ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler();return ob
hero=camera('CAM_01_Front_Left',(-15,-20,14),(0,1,5.35),16)
back=camera('CAM_02_Rear_Right',(15,20,13),(0,1.3,5.6),16)
frontcam=camera('CAM_03_Centred_Front',(0,-23,8.4),(0,1,5.8),14.5)
S.camera=hero;S.render.engine='CYCLES';S.cycles.samples=32;S.cycles.use_denoising=True;S.render.threads_mode='FIXED';S.render.threads=8
S.view_settings.view_transform='AgX';S.render.resolution_x=1200;S.render.resolution_y=1200;S.render.resolution_percentage=100
for ob in bpy.context.selected_objects:ob.select_set(False)
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':
   area.spaces.active.region_3d.view_perspective='CAMERA';area.spaces.active.clip_end=300
S['asset_stage']='Church_A geometry v001 - unpainted';S['front_direction']='-Y';S['reuse_from']='House_Cottage_A'
bpy.ops.wm.save_as_mainfile(filepath=str(O/'Church_A.blend'))
for cam,n in [(hero,'01_Hero'),(back,'02_Rear'),(frontcam,'03_Front')]:
 S.camera=cam;S.render.filepath=str(O/(n+'.png'));bpy.ops.render.render(write_still=True)
print('CHURCH_COMPLETE',flush=True)
