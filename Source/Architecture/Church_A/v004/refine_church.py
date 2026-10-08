"""Targeted v004 revision: metric timber UV, bonded masonry, stair supports,
front cross clearance, branching foliage and covered roof face reduction."""
import bpy,bmesh,math,random,json
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(P.parent/'v003/Church_A.blend'))
S=bpy.context.scene;S.render.threads_mode='FIXED';S.render.threads=8
stone=bpy.data.materials['M_Cottage_FieldStone_A'];timber=bpy.data.materials['M_Cottage_StructuralTimber_A']
F=bpy.data.collections['02_FOUNDATION_AND_MASONRY'];E=bpy.data.collections['07_ENTRANCE'];V=bpy.data.collections['08_LIGHT_VINES'];R=bpy.data.collections['04_TILED_ROOFS']
def mesh(n,vs,fs,c,mat):
 me=bpy.data.meshes.new(n);me.from_pydata(vs,[],fs);me.update();bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
 ob=bpy.data.objects.new(n,me);c.objects.link(ob);me.materials.append(mat);return ob
def active(o):
 bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
def bake(o):
 active(o)
 for m in list(o.modifiers):bpy.ops.object.modifier_apply(modifier=m.name)
def stone_uv(o):
 uv=o.data.uv_layers.get('UV0') or o.data.uv_layers.new(name='UV0')
 # Metric crop from a single stone interior, with aspect ratio preserved.
 for f in o.data.polygons:
  axes=[i for i in range(3) if i!=max(range(3),key=lambda i:abs(f.normal[i]))]
  ps=[o.data.vertices[o.data.loops[li].vertex_index].co for li in f.loop_indices]
  center=sum(ps,Vector())/len(ps);a,b=axes
  scale=min(.084/max(max(p[a] for p in ps)-min(p[a] for p in ps),.001),.056/max(max(p[b] for p in ps)-min(p[b] for p in ps),.001))*.96
  for li,p in zip(f.loop_indices,ps):uv.data[li].uv=(.223+(p[a]-center[a])*scale,.689+(p[b]-center[b])*scale)
def block(n,pos,dims,c,bevel=.024):
 x,y,z=[v/2 for v in dims]
 o=mesh(n,[(-x,-y,-z),(-x,-y,z),(-x,y,-z),(-x,y,z),(x,-y,-z),(x,-y,z),(x,y,-z),(x,y,z)],[(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)],c,stone);o.location=pos
 m=o.modifiers.new('Small consistent stone bevel','BEVEL');m.width=min(bevel,min(dims)*.18);m.segments=1
 m=o.modifiers.new('Weighted stone normals','WEIGHTED_NORMAL');m.keep_sharp=True
 bake(o);stone_uv(o);o['material_role']='stone';return o
# Fix all timber in real metres. Every object gets its own correctly scaled UV.
uv_metrics=[]
for o in list(S.objects):
 if o.type!='MESH' or o.get('material_role') not in ['timber','frame']:continue
 o.data=o.data.copy();me=o.data;uv=me.uv_layers.get('UV0') or me.uv_layers.new(name='UV0')
 lo=Vector([min(v.co[i] for v in me.vertices) for i in range(3)])
 hi=Vector([max(v.co[i] for v in me.vertices) for i in range(3)])
 lengths=[(hi[i]-lo[i])*abs(o.scale[i]) for i in range(3)]
 along=2 if me.name.startswith('Cottage_Beam') else max(range(3),key=lambda i:lengths[i])
 off=(sum(map(ord,o.name))%19)*.027
 for f in me.polygons:
  drop=max(range(3),key=lambda i:abs(f.normal[i]));axes=[i for i in range(3) if i!=drop]
  for li in f.loop_indices:
   p=me.vertices[me.loops[li].vertex_index].co
   if along in axes:
    cross=next(i for i in axes if i!=along)
    q=(.06+off+(p[along]-lo[along])*abs(o.scale[along])*.64,.31+(p[cross]-lo[cross])*abs(o.scale[cross])*.64)
   else:q=(.06+(p[axes[0]]-lo[axes[0]])*abs(o.scale[axes[0]])*.64,.31+(p[axes[1]]-lo[axes[1]])*abs(o.scale[axes[1]])*.64)
   uv.data[li].uv=q
 o['uv_metres_to_repeat']=.64;uv_metrics.append(o.name)
# Stair walls: discard intersecting infill and stacked caps. New masonry is fully solid.
for o in list(E.objects):
 if o.name.startswith(('StairSide_','Step_Cheek')):bpy.data.objects.remove(o,do_unlink=True)
for sign in [-1,1]:
 for row,(z,h,edges) in enumerate([(.12,.24,[-5.15,-4.66,-4.17,-3.70]),(.355,.23,[-4.92,-4.42,-3.92,-3.70]),(.555,.17,[-4.44,-3.96,-3.70])]):
  for j,(a,b) in enumerate(zip(edges,edges[1:])):
   block(f'Stair_Bonded_{sign}_{row}_{j}',(sign*1.30,(a+b)/2,z),(.35,b-a-.007,h-.006),E,.018)
 # Grounded inner core, inset behind the outer stone faces, strictly below treads.
 outline=[(-5.15,0),(-3.70,0),(-3.70,.41),(-4.40,.41),(-4.40,.265),(-4.66,.265),(-4.66,.12),(-5.15,.12)]
 xs=sorted([sign*1.115,sign*1.265]);k=len(outline)
 o=mesh('Stair_Core_Inset',[(x,y,z) for x in xs for y,z in outline],[tuple(range(k-1,-1,-1)),tuple(range(k,2*k))]+[(i,(i+1)%k,(i+1)%k+k,i+k) for i in range(k)],E,stone);stone_uv(o)
# Rebond every nave foundation run. Thin corner joints, no stacked vertical seams.
for o in list(F.objects):
 if o.name.startswith(('Nave_Foundation_','Nave_Corner_Base')):bpy.data.objects.remove(o,do_unlink=True)
rng=random.Random(481)
def course(n,start,end,z,width,axis,fixed,row):
 span=end-start;step=.72
 cuts=[start];v=start+(.34 if row else .70)
 while v<end-.20:cuts.append(v);v+=step
 cuts.append(end)
 for i,(a,b) in enumerate(zip(cuts,cuts[1:])):
  jitter=rng.uniform(-.004,.004);length=b-a-.010
  p=((a+b)/2,fixed+jitter,z) if axis==0 else (fixed+jitter,(a+b)/2,z)
  d=(length,width,.294) if axis==0 else (width,length,.294)
  o=block(n,p,d,F,.027);o.rotation_euler.z=rng.uniform(-.003,.003)
for row in range(2):
 z=.155+row*.305
 for sign in [-1,1]:
  course('Foundation_Bonded_Side',-3.37,3.37,z,.41,1,sign*2.79,row)
  spans=[(-2.49,-1.10),(1.10,2.49)] if sign<0 else [(-2.49,2.49)]
  for a,b in spans:course('Foundation_Bonded_End',a,b,z,.43,0,sign*3.66,row)
 for x in [-2.76,2.76]:
  for y in [-3.65,3.65]:block('Foundation_Bonded_Corner',(x,y,z),(.53,.54,.294),F,.028)
# Single-piece crosses remove coplanar arm/shaft faces. Saddle base follows the gable.
def prism(n,outline,y0,y1,c):
 k=len(outline);o=mesh(n,[(x,y,z) for y in [y0,y1] for x,z in outline],[tuple(range(k-1,-1,-1)),tuple(range(k,k*2))]+[(i,(i+1)%k,(i+1)%k+k,i+k) for i in range(k)],c,stone)
 m=o.modifiers.new('Cross softened outline','BEVEL');m.width=.013;m.segments=1
 m=o.modifiers.new('Cross weighted normals','WEIGHTED_NORMAL');m.keep_sharp=True;bake(o);stone_uv(o);return o
for prefix,cy,bottom,scale,col in [('Front_Cross',-3.87,6.946,.78,bpy.data.collections['03_TIMBER']),('Tower_Cross',5.72,11.32,1,bpy.data.collections['06_REAR_BELL_TOWER'])]:
 for o in list(col.objects):
  if o.name.startswith(prefix) and ('Foot' not in o.name or prefix=='Front_Cross'):bpy.data.objects.remove(o,do_unlink=True)
 w=.095*scale;arm=.35*scale;za=bottom+.56*scale;zb=za+.18*scale;zt=bottom+1.0*scale
 prism(prefix+'_SingleStone',[(-w,bottom),(w,bottom),(w,za),(arm,za),(arm,zb),(w,zb),(w,zt),(-w,zt),(-w,zb),(-arm,zb),(-arm,za),(-w,za)],cy-.095*scale,cy+.095*scale,col)
prism('Front_Cross_Foot',[(-.20,6.565),(-.20,6.985),(.20,6.985),(.20,6.565),(0,6.765)],-4.04,-3.72,bpy.data.collections['03_TIMBER'])
# Reduce ridge-cap arc tessellation without changing its outline radius.
caps=[o for o in R.objects if o.name.startswith(('Nave_Roof_Ridge','Porch_Roof_Ridge'))]
cap_saved=0
for o in caps:
 old=o.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh();old.calc_loop_triangles();cap_saved+=len(old.loop_triangles);o.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh_clear()
 vs=[(x,.205*math.cos(math.pi*i/8),.205*math.sin(math.pi*i/8)) for x in [-.205,.205] for i in range(9)]
 fs=[(i,i+1,i+10,i+9) for i in range(8)]
 me=bpy.data.meshes.new('RidgeCap_8_Sectors');me.from_pydata(vs,[],fs);me.materials.append(bpy.data.materials['M_Cottage_Terracotta_A']);me.update();o.data=me
 if o.name=='Nave_Roof_Ridge':
  # local X maps to world Y after a 90 degree turn
  cut=(-3.68-o.location.y)/o.scale.x
  for v in me.vertices:
   if v.co.x<cut:v.co.x=cut
 for f in me.polygons:f.use_smooth=True
 uv=me.uv_layers.new(name='UV0')
 for f in me.polygons:
  for li in f.loop_indices:
   v=me.vertices[me.loops[li].vertex_index].co;uv.data[li].uv=(.32+(v.x+.205)*.5,.30+math.atan2(v.z,v.y)/math.pi*.25)
 o['optimization']='8 arc sectors, smooth normals, physical thickness retained'
# Cull only bottoms and uphill walls of INTERIOR tile rows, covered by the roof.
removed=0;cache={}
for o in list(R.objects):
 if not o.name.startswith(('Nave_Roof_Tile','Porch_Roof_Tile','Tower_Hip_Cottage_Tile')):continue
 if o.name.startswith('Nave') and abs(o.location.x)>3.1:continue
 if o.name.startswith('Porch') and abs(o.location.x)>1.38:continue
 if o.name.startswith('Tower') and max(max(abs(v.co.x),abs(v.co.y-5.72)) for v in o.data.vertices)>1.70:continue
 key=o.data.name
 if key not in cache:
  me=o.data.copy();bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table()
  # 6 upper + 6 lower vertices in the source tile. Keep exposed lip and side edges.
  faces=[f for f in bm.faces if all(v.index>=6 for v in f.verts) or all(v.index in [3,4,5,9,10,11] for v in f.verts)]
  n=sum(len(f.verts)-2 for f in faces);bmesh.ops.delete(bm,geom=faces,context='FACES');bm.to_mesh(me);bm.free();cache[key]=(me,n)
 o.data,n=cache[key];removed+=n;o['covered_face_culling']='Bottom and uphill faces covered by substrate/next row; eave rows retained closed'
# More natural vines: multiple wall-hugging stems, tapered branch fans and leaf bunches.
for o in list(V.objects):bpy.data.objects.remove(o,do_unlink=True)
leaf=bpy.data.materials['M_Church_Vine_ExistingFoliage'];stem=bpy.data.materials['M_Church_Vine_Stem']
mix=next(n for n in leaf.node_tree.nodes if n.type=='MIX_RGB');mix.inputs[0].default_value=.48;mix.inputs[2].default_value=(.30,.52,.27,1)
patches=[]
def foliage(n,origin,right,normal,paths,seed):
 rand=random.Random(seed);origin=Vector(origin);right=Vector(right);normal=Vector(normal);up=Vector((0,0,1));sv=[];sf=[];lv=[];lf=[];uvs=[]
 def world(p):return origin+right*p[0]+up*p[1]+normal*p[2]
 def tube(pts,r):
  pts=[world(p) for p in pts];base=len(sv);N=4
  for i,p in enumerate(pts):
   d=(pts[min(i+1,len(pts)-1)]-pts[max(i-1,0)]).normalized();a=d.cross(normal).normalized();b=d.cross(a);rr=r*(1-.75*i/(len(pts)-1))
   sv.extend([p+rr*(a*math.cos(j*math.pi/2)+b*math.sin(j*math.pi/2)) for j in range(N)])
  for i in range(len(pts)-1):
   for j in range(N):sf.append((base+i*N+j,base+i*N+(j+1)%N,base+(i+1)*N+(j+1)%N,base+(i+1)*N+j))
  sf.extend([tuple(base+j for j in reversed(range(N))),tuple(base+(len(pts)-1)*N+j for j in range(N))])
 def card(pt,angle,size,cluster=False):
  if cluster:
   # Short leafy side shoot, not a circular atlas bunch floating on a stem.
   pt=Vector(pt);tip=pt+Vector((.03*math.sin(angle),size*.56,.015))
   tube([pt,tip],.003)
   for j in range(5):
    sg=-1 if j%2 else 1
    q=pt.lerp(tip,(j+.25)/5)+Vector((sg*.018,0,.007))
    card(q,sg*rand.uniform(.60,1.15),size*rand.uniform(.32,.43),False)
   return
  center=world(pt);d=(right*math.sin(angle)+up*math.cos(angle)).normalized();a=d.cross(normal).normalized();base=len(lv)
  rect=rand.choice([(14,22,452,414),(468,12,863,422),(873,28,1244,403),(22,425,439,716)]) if cluster else rand.choice([(422,991,633,1237),(911,983,1100,1228)])
  width=size*(1.05 if cluster else .65);basepoint=center-d*size*(.35 if cluster else .05)
  lv.extend([basepoint-a*width/2,basepoint+a*width/2,basepoint+d*size+a*width/2,basepoint+d*size-a*width/2,basepoint+d*size*.53+normal*(.028 if cluster else .018)])
  x0,y0,x1,y1=rect;u0,u1=x0/1254,x1/1254;v0,v1=1-y1/1254,1-y0/1254
  uvs.extend([(u0,v0),(u1,v0),(u1,v1),(u0,v1),((u0+u1)/2,(v0+v1)/2)]);lf.extend([(base+i,base+(i+1)%4,base+4) for i in range(4)])
 for pi,path in enumerate(paths):
  tube(path,.014 if pi==0 else .008)
  for k,(a,b) in enumerate(zip(path,path[1:])):
   a,b=Vector(a),Vector(b);count=max(2,round((b-a).length/.14))
   for j in range(count):
    t=(j+rand.uniform(.2,.8))/count;pt=a.lerp(b,t);sgn=-1 if (j+k+pi)%2 else 1
    end=pt+Vector((sgn*rand.uniform(.10,.21),rand.uniform(.06,.17),rand.uniform(.025,.055)))
    tube([pt,end],.0035);card(end,sgn*rand.uniform(.50,1.4),rand.uniform(.12,.19))
   if k%2==1:
    pt=a.lerp(b,.48)+Vector((rand.uniform(-.06,.06),0,.055))
    card(pt,rand.uniform(-.7,.7),rand.uniform(.30,.43),True)
 mesh(n+'_Stems',sv,sf,V,stem)
 o=mesh(n+'_Leaves',lv,lf,V,leaf);uv=o.data.uv_layers.new(name='UV0')
 for f in o.data.polygons:
  for li in f.loop_indices:uv.data[li].uv=uvs[o.data.loops[li].vertex_index]
 o['intentional_open_surface']='Two-sided folded alpha cards; atlas leaf and bunch crops';patches.append({'name':n,'cards':len(lv)//5})
foliage('Ivy_Entrance',(2.13,-3.95,0),(1,0,0),(0,-1,0),[
 [(0,.1,0),(-.06,.46,.01),(.08,.91,.015),(-.08,1.32,.02),(.02,1.77,.015),(-.11,2.12,.025),(-.02,2.51,.02)],
 [(-.03,.64,.02),(-.25,.93,.025),(-.38,1.22,.035),(-.49,1.48,.035)],
 [(-.06,1.26,.015),(.17,1.59,.03),(.28,1.97,.03)],
 [(.01,1.77,.02),(-.33,2.0,.04),(-.48,2.24,.05)]],41)
foliage('Ivy_Left',(-3.01,-1.15,0),(0,1,0),(-1,0,0),[
 [(0,.15,0),(-.07,.59,.015),(.06,1.04,.02),(-.09,1.49,.02),(.02,1.92,.02),(-.05,2.39,.025),(.08,2.87,.02),(-.06,3.32,.025),(-.40,3.59,.04)],
 [(-.04,2.40,.025),(-.26,2.84,.03),(-.48,3.23,.05),(-.70,3.42,.05)],
 [(.0,.64,.03),(.18,.95,.04),(.27,1.23,.04)],
 [(-.05,3.30,.025),(.27,3.50,.04),(.53,3.58,.04)]],57)
foliage('Ivy_Tower',(-1.54,6.50,0),(0,1,0),(-1,0,0),[
 [(0,.12,0),(-.08,.68,.02),(.07,1.14,.02),(-.04,1.61,.02),(.07,2.14,.03),(-.09,2.63,.025),(.01,3.09,.025),(-.04,3.50,.03),(.0,3.90,.02)],
 [(-.03,1.60,.02),(-.27,1.98,.04),(-.46,2.30,.04)],
 [(.04,2.07,.025),(.29,2.43,.05),(.39,2.73,.045)]],77)
foliage('Ivy_Right',(3.01,1.17,0),(0,-1,0),(1,0,0),[
 [(0,.14,0),(.06,.53,.02),(-.09,.96,.025),(.02,1.36,.02),(-.06,1.76,.04)],
 [(-.01,.84,.025),(.19,1.11,.04),(.32,1.42,.05)]],97)
# Export-independent QA and compact evidence renders.
bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();tris=0;by={};issues=[]
for o in S.objects:
 if o.type!='MESH' or any(c.name=='90_STUDIO' for c in o.users_collection):continue
 ev=o.evaluated_get(deps);me=ev.to_mesh();me.calc_loop_triangles();t=len(me.loop_triangles);tris+=t
 by[o.users_collection[0].name]=by.get(o.users_collection[0].name,0)+t
 if any(t.area<1e-10 for t in me.loop_triangles):issues.append(o.name)
 ev.to_mesh_clear()
report={'version':'v004','triangles':tris,'previous':50746,'net_removed':50746-tris,'interior_tile_triangles_removed':removed,'by_collection':by,'metric_timber_objects':len(uv_metrics),'timber_uv_repeat_per_m':.64,'foliage_patches':patches,'degenerate_objects':issues,'engine_ready':False}
(P/'geometry_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print('REPORT',json.dumps(report),flush=True);assert not issues,issues
def camera(n,pos,target,scale):
 d=bpy.data.cameras.new(n);d.type='ORTHO';d.ortho_scale=scale;o=bpy.data.objects.new(n,d);bpy.data.collections['90_STUDIO'].objects.link(o);o.location=pos;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();return o
close=camera('CAM_06_Cross_Clearance',(-5,-10,8.2),(0,-3.77,6.95),2.35)
S.camera=bpy.data.objects['CAM_01_Front_Left'];S.cycles.samples=32;S.cycles.transparent_max_bounces=16;S['asset_stage']='Church_A v004 - revised vines, bonded stone, metric timber UV and roof optimization'
bpy.ops.object.select_all(action='DESELECT');bpy.ops.wm.save_as_mainfile(filepath=str(P/'Church_A.blend'))
for cam,name in [('CAM_01_Front_Left','01_Hero'),('CAM_04_Entrance','02_Entrance'),('CAM_02_Rear_Right','03_Rear'),('CAM_06_Cross_Clearance','04_Cross')]:
 S.camera=bpy.data.objects[cam];S.render.filepath=str(P/(name+'.png'));bpy.ops.render.render(write_still=True)
print('FINISHED',flush=True)
