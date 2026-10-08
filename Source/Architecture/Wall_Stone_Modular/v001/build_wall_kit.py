"""Deterministic Blender 4.4 authoring/export/QA. Run Blender -b -t 6 -P this.py.

Author in Blender Z-up; U(x,y,z) -> B(x,-z,y). FBX is Y-up, -Z-forward.
Only generated files below this version directory are replaced on rebuild.
"""
import bpy, bmesh, math, json, random, hashlib, shutil, sys
from array import array
from pathlib import Path
from mathutils import Vector, Matrix

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
WORKSPACE = REPO.parent
NAMES = ['SM_Wall_Stone_2m_A', 'SM_Wall_Stone_1m_A',
         'SM_Wall_Stone_Pillar_A', 'SM_Wall_Stone_End_A',
         'SM_Wall_Banner_Cloth_A', 'SM_Wall_Banner_Bracket_A']
PATCHES = [(150,40,345,115), (690,40,835,115), (545,355,705,425)]
UV_DENSITY = .5  # One original tile per 2 metres, ALL stone faces/LODs.
ASSETS = {}
REPORT = {'blender': bpy.app.version_string, 'seed': 7319, 'assets': {},
          'unity_tested': False, 'uv_units_per_metre': UV_DENSITY}

def B(p):
    return Vector((p[0], -p[2], p[1]))

def U(p):
    return [p[0], p[2], -p[1]]

def collection(name):
    c = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(c)
    return c

def material(name, color, roughness=.88, metallic=0):
    m=bpy.data.materials.new(name); m.use_nodes=True; m.diffuse_color=(*color,1)
    bs=m.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value=(*color,1)
    bs.inputs['Roughness'].default_value=roughness
    bs.inputs['Metallic'].default_value=metallic
    return m

def load_stone():
    m=material('M_Wall_Stone_Shared', (.62,.53,.40))
    nodes=m.node_tree.nodes; links=m.node_tree.links; bs=nodes.get('Principled BSDF')
    for channel in ['BaseColor','Normal','Roughness']:
        im=bpy.data.images.load(str(HERE/'Textures'/f'StoneWall_A_{channel}_2048.png'))
        im.colorspace_settings.name='sRGB' if channel=='BaseColor' else 'Non-Color'
        tex=nodes.new('ShaderNodeTexImage'); tex.image=im
        tex.location=(-650, {'BaseColor':300,'Normal':0,'Roughness':-300}[channel])
        if channel=='BaseColor':
            links.new(tex.outputs['Color'],bs.inputs['Base Color'])
        elif channel=='Normal':
            normal=nodes.new('ShaderNodeNormalMap'); normal.inputs['Strength'].default_value=.12
            links.new(tex.outputs['Color'],normal.inputs['Color']); links.new(normal.outputs[0],bs.inputs['Normal'])
        else:
            links.new(tex.outputs['Color'],bs.inputs['Roughness'])
    m['source_asset_id']='MAT_StoneWall_A_Unity'
    m['source_maps']='User-selected CozySettlement/Mat/StoneWall_A_Unity, copied byte-for-byte'
    global HEIGHT_PIXELS, HEIGHT_SIZE
    im=bpy.data.images.load(str(HERE/'Textures/StoneWall_A_Height_2048.png'))
    im.colorspace_settings.name='Non-Color';HEIGHT_SIZE=im.size[0]
    HEIGHT_PIXELS=array('f',[0])*(len(im.pixels));im.pixels.foreach_get(HEIGHT_PIXELS)
    return m

class Geometry:
    def __init__(self): self.v=[]; self.f=[]; self.patches=[]; self.uvs=[]
    def face(self,points,patch=0,uv=None):
        start=len(self.v); self.v.extend(points)
        self.f.append(tuple(range(start,start+len(points)))); self.patches.append(patch);self.uvs.append(uv)
    def box(self,lo,hi,patch=0,omit=()):
        v=[(x,y,z) for x in (lo[0],hi[0]) for y in (lo[1],hi[1]) for z in (lo[2],hi[2])]
        for name,ids in [('x-',(0,1,3,2)),('x+',(4,6,7,5)),('y-',(0,4,5,1)),
                         ('y+',(2,3,7,6)),('z-',(0,2,6,4)),('z+',(1,5,7,3))]:
            if name not in omit: self.face([v[i] for i in ids],patch)
    def panel(self,u0,u1,v0,v1,plane,depth,lod,patch):
        # Surface-only masonry: mortar border -> bevel -> slightly irregular face.
        # No separate stone backs or buried cubes.
        outer=[(u0,v0),(u1,v0),(u1,v1),(u0,v1)]
        if lod==2:
            self.face([plane(u,v,depth) for u,v in outer],patch); return
        gap=.005; bevel=.012 if lod==0 else .009
        ring=[(u0+gap,v0+gap),(u1-gap,v0+gap),(u1-gap,v1-gap),(u0+gap,v1-gap)]
        front=[(u0+gap+bevel,v0+gap+bevel),(u1-gap-bevel,v0+gap+bevel),
               (u1-gap-bevel,v1-gap-bevel),(u0+gap+bevel,v1-gap-bevel)]
        # Uniform seed creates reproducible nicks without touching module bounds.
        rng=random.Random(round(u0*10000)+round(v0*9731)+patch*191)
        if lod==0:
            front=[(u+rng.uniform(-.0025,.0025),v+rng.uniform(-.0025,.0025)) for u,v in front]
        rings=[outer,ring,front] if lod==0 else [outer,front]
        ds=[0,depth-.007,depth] if lod==0 else [0,depth]
        for r in range(len(rings)-1):
            for i in range(4):
                j=(i+1)%4
                self.face([plane(*rings[r][i],ds[r]),plane(*rings[r][j],ds[r]),
                           plane(*rings[r+1][j],ds[r+1]),plane(*rings[r+1][i],ds[r+1])],patch)
        self.face([plane(u,v,depth) for u,v in front],patch)
    def mesh(self,name,coll,mat):
        me=bpy.data.meshes.new(name); me.from_pydata([B(p) for p in self.v],[],self.f); me.update()
        uv=me.uv_layers.new(name='UV0')
        for poly,patch,override in zip(me.polygons,self.patches,self.uvs):
            if override is not None:
                for li,p in zip(poly.loop_indices,override):uv.data[li].uv=p
                continue
            verts=[me.vertices[me.loops[i].vertex_index].co for i in poly.loop_indices]
            n=poly.normal
            # Orthonormal projection preserves actual density even on bevel faces.
            t=(verts[1]-verts[0]).normalized(); bt=n.cross(t).normalized()
            coords=[Vector((p.dot(t),p.dot(bt))) for p in verts]
            center=sum(coords,Vector((0,0)))/len(coords)
            origin=Vector([(0.40,0.74),(0.76,0.74),(0.36,0.50)][patch%3])
            for li,p in zip(poly.loop_indices,coords): uv.data[li].uv=origin+(p-center)*UV_DENSITY
        # Weld repeated surface borders and make normals consistent where connected.
        bm=bmesh.new(); bm.from_mesh(me)
        bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6)
        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
        bmesh.ops.triangulate(bm,faces=list(bm.faces)); bm.to_mesh(me); bm.free()
        ob=bpy.data.objects.new(name,me); coll.objects.link(ob); me.materials.append(mat)
        return ob

def bevel_box(g,lo,hi,patch,lod,bevel=.018,top_slope=0):
    # A beveled slab exported as one shell; no modifier-dependent geometry.
    x0,y0,z0=lo; x1,y1,z1=hi
    b=min(bevel,min(x1-x0,y1-y0,z1-z0)*.19) if lod<2 else 0
    if not b:
        start=len(g.v);g.box(lo,hi,patch)
        if top_slope:
            for i in range(start,len(g.v)):
                x,y,z=g.v[i]
                if abs(y-y1)<1e-6:g.v[i]=(x,y-top_slope*(z-z0)/(z1-z0),z)
        return
    # Square corner chamfers, top and bottom bevel rings.
    def ring(x0,x1,z0,z1,y,c):
        return [(x0+c,y,z0),(x1-c,y,z0),(x1,y,z0+c),(x1,y,z1-c),
                (x1-c,y,z1),(x0+c,y,z1),(x0,y,z1-c),(x0,y,z0+c)]
    rings=[ring(x0+b,x1-b,z0+b,z1-b,y0,b/2),ring(x0,x1,z0,z1,y0+b,b),
           ring(x0,x1,z0,z1,y1-b,b),ring(x0+b,x1-b,z0+b,z1-b,y1,b/2)]
    if top_slope:
        rings=[[ (x,y-top_slope*min(1,max(0,(z-z0-b)/(z1-z0-2*b))) if y>y0+b+.001 else y,z)
                for x,y,z in r] for r in rings]
    for r in range(3):
        for i in range(8):
            j=(i+1)%8;g.face([rings[r][i],rings[r][j],rings[r+1][j],rings[r+1][i]],patch)
    g.face(list(reversed(rings[0])),patch);g.face(rings[-1],patch)

def masonry(g,length,width,y0,y1,lod,rows,seed,ends=True):
    # Closed surface, relief sampled from the chosen stone map (not another brick grid).
    # No hidden individual-stone backs. Borders stay fixed for gap-free stitching.
    nu=max(2,round(length*[18,9,2][lod]));nv=max(2,round((y1-y0)*[18,9,2][lod]))
    for side in [-1,1]:
        verts=[];uvs=[]
        for j in range(nv+1):
            y=y0+(y1-y0)*j/nv
            for i in range(nu+1):
                z=-length/2+length*i/nu;u=z*UV_DENSITY+.5;v=y*UV_DENSITY
                px=int((u%1)*(HEIGHT_SIZE-1));py=int((v%1)*(HEIGHT_SIZE-1))
                h=HEIGHT_PIXELS[(py*HEIGHT_SIZE+px)*4]
                fade=min(1,max(0,(length/2-abs(z)-.10)/.08),j/max(1,nv*.1),(nv-j)/max(1,nv*.1))
                d=(h-.5)*.024*fade if lod<2 else 0
                verts.append((side*(width/2-.014+d),y,z));uvs.append((u,v))
        for j in range(nv):
            for i in range(nu):
                k=j*(nu+1)+i;ids=[k,k+1,k+nu+2,k+nu+1]
                g.face([verts[k] for k in ids],uv=[uvs[k] for k in ids])
    for side in [-1,1]:
        for j in range(nv):
            ya=y0+(y1-y0)*j/nv;yb=y0+(y1-y0)*(j+1)/nv;x=width/2-.014
            points=[(-x,ya,side*length/2),(x,ya,side*length/2),(x,yb,side*length/2),(-x,yb,side*length/2)]
            g.face(points,uv=[(p[0]*UV_DENSITY+.5,p[1]*UV_DENSITY) for p in points])
    for y in [y0,y1]:
        for i in range(nu):
            za=-length/2+length*i/nu;zb=-length/2+length*(i+1)/nu;x=width/2-.014
            points=[(-x,y,za),(x,y,za),(x,y,zb),(-x,y,zb)]
            g.face(points,uv=[(p[2]*UV_DENSITY+.5,p[0]*UV_DENSITY+.5) for p in points])

def wall(length,lod):
    g=Geometry()
    masonry(g,length,.58,.09,1.02,lod,4,130+int(length))
    # Continuous squared join ends; seam cannot open from a rounded end cap.
    for ya,yb,w in [(0,.10,.60),(1.02,1.14,.60)]:
        steps=max(1,round(length/.5))
        for i in range(steps):
            a=-length/2+i*length/steps; b=-length/2+(i+1)*length/steps
            # Slabs remain within nominal length; bevel is small enough for overlap.
            bevel_box(g,(-w/2,ya,a),(w/2,yb,b),i%3,lod,.010)
    n=3 if length==2 else 2
    merlon_width=.36 if length==2 else .28
    for i in range(n):
        z=(-length/2+.10+merlon_width/2)+(length-.20-merlon_width)*i/(n-1)
        bevel_box(g,(-.272,1.14,z-merlon_width/2),(.272,1.35,z+merlon_width/2),i,lod,.018)
        bevel_box(g,(-.29,1.35,z-merlon_width/2),(.29,1.40,z+merlon_width/2),i,lod,.009)
    # A small inward end taper prevents coplanar overlapping side faces from
    # z-fighting. It fits entirely within the quiet 10 cm connection band.
    for i,(x,y,z) in enumerate(g.v):
        fade=max(0,1-(length/2-abs(z))/.10)
        g.v[i]=(x*(1-.035*fade),y,z)
    return g

def pillar(lod):
    g=Geometry(); masonry(g,.60,.64,.13,1.36,lod,6,716)
    # Inset shaft, solid projecting cap and low pitched top.
    bevel_box(g,(-.35,0,-.35),(.35,.14,.35),0,lod,.02)
    bevel_box(g,(-.325,1.33,-.325),(.325,1.40,.325),1,lod,.012)
    bevel_box(g,(-.35,1.40,-.35),(.35,1.51,.35),0,lod,.018)
    corners=[(-.328,1.51,-.328),(.328,1.51,-.328),(.328,1.51,.328),(-.328,1.51,.328)]
    top=[(-.19,1.60,-.19),(.19,1.60,-.19),(.19,1.60,.19),(-.19,1.60,.19)]
    for i in range(4): g.face([corners[i],corners[(i+1)%4],top[(i+1)%4],top[i]],i%3)
    g.face(top,0)
    return g

def endcap(lod):
    g=Geometry();masonry(g,.56,.56,.10,1.14,lod,5,203)
    bevel_box(g,(-.30,0,-.30),(.30,.10,.30),0,lod,.015)
    bevel_box(g,(-.30,1.14,-.30),(.30,1.40,.30),1,lod,.012,.18)
    return g

def cloth(lod,coll,mat):
    nx,ny=[(8,12),(4,6),(2,3)][lod]; verts=[]; faces=[]
    for j in range(ny+1):
        for i in range(nx+1):
            u=i/nx;v=j/ny
            depth=.008+.008*math.sin(u*math.pi*4)*math.sin(v*math.pi/2)+.004*v
            verts.append(B(((u-.5)*.36,-v*.55,depth)))
    for j in range(ny):
        for i in range(nx):
            k=j*(nx+1)+i; faces.append((k,k+nx+1,k+nx+2,k+1))
    front_count=len(verts)
    verts += [p+B((0,0,-.001)) for p in verts[:]]
    faces += [tuple(i+front_count for i in reversed(f)) for f in faces[:]]
    me=bpy.data.meshes.new('BannerCloth');me.from_pydata(verts,[],faces);me.update()
    uv=me.uv_layers.new(name='UV0')
    for p in me.polygons:
        p.use_smooth=True
        for li in p.loop_indices:
            idx=me.loops[li].vertex_index;k=idx%front_count
            u=k%(nx+1)/nx
            uv.data[li].uv=(u if idx<front_count else 1-u,1-k//(nx+1)/ny)
    ob=bpy.data.objects.new(f'{NAMES[4]}_LOD{lod}',me);coll.objects.link(ob);me.materials.append(mat)
    return ob

def bracket(lod):
    g=Geometry()
    if lod==2:
        g.box((-.21,-.004,.029),(.21,.014,.047))
        for x in [-.15,.15]:g.box((x-.025,-.04,0),(x+.025,.025,.038))
        return g
    for x in [-.15,.15]:
        bevel_box(g,(x-.025,-.04,0),(x+.025,.025,.015),0,0 if lod==0 else 2,.005)
        bevel_box(g,(x-.009,-.006,.01),(x+.009,.012,.047),0,0 if lod==0 else 2,.004)
    bevel_box(g,(-.21,-.004,.029),(.21,.014,.047),0,0 if lod==0 else 2,.004)
    return g

def bounds(ob):
    pts=[U(v.co) for v in ob.data.vertices]
    lo=[min(p[i] for p in pts) for i in range(3)];hi=[max(p[i] for p in pts) for i in range(3)]
    return {'min':lo,'max':hi,'size':[hi[i]-lo[i] for i in range(3)]}

def audit(ob):
    me=ob.data;me.calc_loop_triangles();uv=me.uv_layers.active
    errors=[];min_area=1e8;min_uv=1e8
    for tri in me.loop_triangles:
        a,b,c=[me.vertices[i].co for i in tri.vertices];area=(b-a).cross(c-a).length/2
        q,r,s=[uv.data[i].uv for i in tri.loops];ua=abs((r.x-q.x)*(s.y-q.y)-(r.y-q.y)*(s.x-q.x))/2
        min_area=min(area,min_area);min_uv=min(ua,min_uv)
    if min_area<1e-10:errors.append('zero geometry area')
    if min_uv<1e-12:errors.append('zero UV area')
    if len(me.materials)!=1:errors.append('material count')
    assert not errors,(ob.name,errors)
    return dict(bounds(ob),triangles=len(me.loop_triangles),vertices=len(me.vertices),
                material=me.materials[0].name,min_triangle_area=min_area,min_uv_area=min_uv,
                identity_transform=all(abs(ob.matrix_local[i][j]-(1 if i==j else 0))<1e-6 for i in range(4) for j in range(4)))

def build_assets():
    stone=load_stone();fabric=material('M_PlayerBanner',(1,1,1),.96)
    iron=material('M_BannerBracket_Shared',(.12,.105,.085),.65,.5)
    for idx,name in enumerate(NAMES):
        coll=collection(name);root=bpy.data.objects.new(name,None);coll.objects.link(root)
        root.empty_display_size=.08;root['unity_axes']='Y up, length +Z; source Blender Z up'
        lods=[]
        for lod in range(3):
            if idx==4: ob=cloth(lod,coll,fabric)
            else:
                g=[lambda:wall(2,lod),lambda:wall(1,lod),lambda:pillar(lod),
                   lambda:endcap(lod),None,lambda:bracket(lod)][idx]()
                ob=g.mesh(f'{name}_LOD{lod}',coll,iron if idx==5 else stone)
            ob.parent=root;ob['lod_level']=lod;ob['unity_pivot']='base centre' if idx<4 else 'top centre'
            lods.append(ob)
        extras=[]
        if idx<4:
            dims=[(.60,1.40,2),(.60,1.40,1),(.70,1.60,.70),(.60,1.40,.60)][idx]
            g=Geometry();g.box((-dims[0]/2,0,-dims[2]/2),(dims[0]/2,dims[1],dims[2]/2))
            ob=g.mesh('UCX_'+name,coll,stone);ob.parent=root;ob.hide_render=True;ob.display_type='WIRE';extras.append(ob)
            ob['unity_import_note']='Reference proxy only. Unity does not auto-convert UCX; create BoxCollider and remove proxy renderer.'
        if idx in [0,2]:
            x,h=(.31,1.18) if idx==0 else (.36,1.38)
            for sign,label in [(1,'XPlus'),(-1,'XMinus')]:
                ob=bpy.data.objects.new('BannerAnchor_'+label,None);coll.objects.link(ob);ob.parent=root
                ob.location=B((sign*x,h,0));ob.rotation_euler=(0,0,sign*math.pi/2)
                ob.empty_display_type='ARROWS';ob.empty_display_size=.09
                ob['export_name']='BannerAnchor_'+label;extras.append(ob)
        ASSETS[name]={'root':root,'lods':lods,'extras':extras,'collection':coll}
        REPORT['assets'][name]=[audit(ob) for ob in lods]
        assert all(REPORT['assets'][name][i]['triangles']>=REPORT['assets'][name][i+1]['triangles'] for i in range(2))
    bpy.context.view_layer.update()

def export_all():
    for a in ASSETS.values():
        for ob in a['extras']:
            if 'export_name' in ob:ob.name=a['root'].name+'__'+ob['export_name']
    for name,a in ASSETS.items():
        renamed=[]
        for ob in a['extras']:
            if 'export_name' in ob:renamed.append((ob,ob.name));ob.name=ob['export_name']
        bpy.ops.object.select_all(action='DESELECT')
        for ob in [a['root']]+a['lods']+a['extras']:
            ob.hide_set(False);ob.select_set(True)
        bpy.context.view_layer.objects.active=a['root']
        bpy.ops.export_scene.fbx(filepath=str(HERE/'Meshes'/f'{name}.fbx'),use_selection=True,
            object_types={'MESH','EMPTY'},axis_forward='-Z',axis_up='Y',global_scale=1,
            apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',bake_space_transform=True,
            use_mesh_modifiers=True,mesh_smooth_type='FACE',use_tspace=True,
            add_leaf_bones=False,bake_anim=False,path_mode='RELATIVE',embed_textures=False)
        for ob,original in renamed:ob.name=original

def instance(name,pos=(0,0,0),yaw=0,lod=0,mat=None):
    a=ASSETS[name];ob=a['lods'][lod].copy();ob.data=ob.data if mat is None else ob.data.copy()
    STUDIO.objects.link(ob);ob.parent=None;ob.location=B(pos);ob.rotation_euler=(0,0,math.radians(yaw))
    if mat:ob.data.materials.clear();ob.data.materials.append(mat)
    return ob

def banner(pos,yaw,color=None,lod=0):
    instance(NAMES[5],pos,yaw,lod)
    return instance(NAMES[4],pos,yaw,lod,color)

def camera(pos,target,scale):
    data=bpy.data.cameras.new('QA camera'); ob=bpy.data.objects.new('QA camera',data);STUDIO.objects.link(ob)
    ob.location=B(pos);ob.rotation_euler=(B(target)-ob.location).to_track_quat('-Z','Y').to_euler()
    data.type='ORTHO';data.ortho_scale=scale;bpy.context.scene.camera=ob;return ob

def lighting():
    for name,power,size,pos in [('Key',1650,8,(2,9,-4)),('Fill',900,7,(-6,6,1)),('Rim',1800,5,(4,6,7))]:
        d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size
        ob=bpy.data.objects.new(name,d);STUDIO.objects.link(ob);ob.location=B(pos)
        ob.rotation_euler=(-ob.location).to_track_quat('-Z','Y').to_euler()

def reset_studio():
    for ob in list(STUDIO.objects):bpy.data.objects.remove(ob,do_unlink=True)
    sc=bpy.context.scene
    if not sc.world:sc.world=bpy.data.worlds.new('StudioWorld')
    sc.world.color=(.28,.28,.28)
    floor=material('QA_Ground',(.25,.29,.28),.95)
    g=Geometry();g.box((-100,-.055,-100),(100,-.025,100));g.mesh('QA_Ground',STUDIO,floor)
    lighting()

def render(name,pos,target,scale,res=(1500,1000)):
    chosen=next((x.split('=',1)[1].split(',') for x in sys.argv if x.startswith('--previews=')),None)
    if chosen is not None and name not in chosen:return
    sc=bpy.context.scene;cam=camera(pos,target,scale)
    sc.render.resolution_x=res[0];sc.render.resolution_y=res[1]
    bpy.context.view_layer.update();inverse=cam.matrix_world.inverted()
    projected=[inverse@(ob.matrix_world@Vector(p)) for ob in STUDIO.objects
               if ob.type=='MESH' and ob.name!='QA_Ground' for p in ob.bound_box]
    lo=[min(p[i] for p in projected) for i in range(2)];hi=[max(p[i] for p in projected) for i in range(2)]
    cam.location+=cam.matrix_world.to_3x3()@Vector(((lo[0]+hi[0])/2,(lo[1]+hi[1])/2,0))
    cam.data.ortho_scale=max(hi[0]-lo[0],(hi[1]-lo[1])*res[0]/res[1])*1.12
    sc.render.filepath=str(HERE/'Preview'/name)
    bpy.ops.render.render(write_still=True)

def preview_all():
    for a in ASSETS.values(): a['collection'].hide_render=True
    reset_studio()
    # Hero assembly: straight run with pillars + a gentle arc of six rigid pieces.
    for z in [-2.88,-.96,.96]:instance(NAMES[0],(0,0,z))
    for z in [-4.18,2.26]:instance(NAMES[2],(0,0,z))
    prev=Vector((0,0,2.26)); start=prev+Vector((0,0,.26))
    for angle in [0,5,10,15,20,25]:
        direction=Vector((math.sin(math.radians(angle)),0,math.cos(math.radians(angle))))
        center=start+direction*.96;instance(NAMES[0],center,angle);start=center+direction*.96
    instance(NAMES[2],start+direction*.26,25)
    banner((.36,1.38,-4.18),90)
    banner((.36,1.38,2.26),90)
    render('Wall_Modular_Preview.png',(11,9,-9),(0,.55,3),16,(1800,1100))
    reset_studio()
    for name,z in zip(NAMES[:4],[-2.2,.0,1.5,2.6]):instance(name,(0,0,z))
    banner((0,1.3,3.6),90)
    render('Kit_Overview.png',(7,5,-5),(0,.65,.5),7.4,(1600,950))
    reset_studio();instance(NAMES[0]);instance(NAMES[2],(0,0,1.28));banner((.36,1.38,1.28),90)
    render('Stone_and_Banner_Closeup.png',(4,2.6,-2),(.0,.8,.55),3.8,(1300,1100))
    # Mixed lengths, hard corner and curvature QA in one plan-oblique view.
    reset_studio()
    for z in [-3.84,-1.92,0]:instance(NAMES[0],(0,0,z))
    instance(NAMES[1],(0,0,1.42));instance(NAMES[3],(0,0,2.17))
    instance(NAMES[2],(3,0,-2))
    for k in range(2):
        instance(NAMES[0],(3,0,-3.27-1.92*k));instance(NAMES[0],(4.27+1.92*k,0,-2),90)
    render('QA_Mixed_and_Sharp.png',(11,10,-10),(2,.5,-2),11,(1500,1050))
    reset_studio()
    for lod,z in enumerate([-2.8,0,2.8]):instance(NAMES[0],(0,0,z),0,lod)
    render('QA_LOD_Comparison.png',(7,4,-5),(0,.65,0),9,(1500,850))
    # Same mesh + arbitrary colour designs; demo materials are preview-only.
    reset_studio()
    for i,col in enumerate([(.055,.17,.30),(.50,.09,.08),(.13,.31,.16),(.62,.34,.07)]):
        z=-1.35+i*.9;instance(NAMES[2],(0,0,z))
        mat=material('QA_PlayerColour_'+str(i),col)
        banner((.36,1.38,z),90,mat)
    render('QA_Player_Colours.png',(5,2.4,-1.4),(0,.85,0),4.9,(1500,850))
    # Asymmetric UV diagnostic PNG (not a shipped faction emblem).
    reset_studio();im=bpy.data.images.new('QA_Banner_UV_Orientation',width=128,height=128)
    pixels=[]
    for j in range(128):
        for i in range(128):
            col=[(.07,.22,.42),(.7,.12,.07),(.85,.65,.15),(.12,.45,.22)][(1 if i>=64 else 0)+(2 if j>=64 else 0)]
            if 14<i<26 and 24<j<105 or 14<i<62 and 92<j<105 or 14<i<53 and 65<j<78:col=(1,1,1)
            pixels.extend((*col,1))
    im.pixels.foreach_set(pixels);im.filepath_raw=str(HERE/'QA/Banner_UV_Orientation.png');im.file_format='PNG';im.save()
    mat=material('QA_PNG_Only',(1,1,1));tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=im
    mat.node_tree.links.new(tex.outputs['Color'],mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
    for i,lod in enumerate(range(3)):
        instance(NAMES[2],(0,0,(i-1)*.9));banner((.36,1.38,(i-1)*.9),90,mat,lod)
    render('QA_Banner_PNG_LODs.png',(4,1.8,-.7),(0,1.0,0),3.7,(1400,850))

def prepare_inputs():
    for folder in ['Meshes','Textures','Preview','QA','References']: (HERE/folder).mkdir(exist_ok=True,parents=True)
    for p in (WORKSPACE/'CozySettlement/Mat/StoneWall_A_Unity').glob('*'):
        if not p.is_file():continue
        dest=HERE/'Textures'/p.name
        if not dest.exists():shutil.copy2(p,dest)
        assert hashlib.sha256(p.read_bytes()).digest()==hashlib.sha256(dest.read_bytes()).digest()
    ref=Path('C:/Users/Дмитрий/Downloads/Модульная каменная стена_ чертёж поселения.png')
    if ref.exists() and not (HERE/'References/Wall_Concept.png').exists():shutil.copy2(ref,HERE/'References/Wall_Concept.png')

if __name__=='__main__':
    prepare_inputs();bpy.ops.wm.read_factory_settings(use_empty=True)
    sc=bpy.context.scene;sc.unit_settings.system='METRIC';sc.unit_settings.scale_length=1
    sc.render.engine='CYCLES';sc.cycles.samples=24;sc.cycles.use_denoising=True
    sc.render.image_settings.file_format='PNG';sc.render.resolution_percentage=100
    sc.view_settings.view_transform='AgX'
    build_assets();export_all()
    STUDIO=collection('90_PREVIEW_ONLY_DO_NOT_EXPORT');preview_all()
    # Source opens as a clean model gallery with LOD0s, cameras and studio.
    reset_studio()
    for name,z in zip(NAMES[:4],[-2.2,0,1.5,2.6]):instance(name,(0,0,z))
    banner((0,1.3,3.6),90);camera((7,5,-5),(0,.65,.5),7.4)
    for a in ASSETS.values():
        for ob in [a['root']]+a['lods']+a['extras']:ob.hide_set(True)
    bpy.ops.object.select_all(action='DESELECT')
    for im in bpy.data.images:
        if im.source=='FILE':im.pack()
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'Wall_Stone_Modular.blend'))
    (HERE/'QA/geometry_report.json').write_text(json.dumps(REPORT,indent=2),encoding='utf-8')
    print('WALL_KIT_BUILD_COMPLETE',json.dumps({k:[v['triangles'] for v in vs] for k,vs in REPORT['assets'].items()}),flush=True)
