"""Blender 4.4 background authoring. Version-local outputs only; no Unity writes.
Run: blender -b -t 8 -P build_bridge.py. -- --quick skips secondary renders.
"""
import bpy, bmesh, math, random, json, sys, shutil, hashlib
from pathlib import Path
from mathutils import Vector

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
sys.path.insert(0,str(HERE))
import bridge_contract as site
sys.path.insert(0,str(ROOT/'Source/Architecture/Wall_Stone_Modular/v005'))
import wall_geometry as w
G=w.Geometry
RNG=random.Random(site.SEED)
REPORT={'blender':bpy.app.version_string,'unity_tested':False,'meshes':{},'contract':site.validate()}
LODS=[]

def append(dst,src):
    for face,patch,uv in zip(src.f,src.patches,src.uvs):
        dst.face([src.v[i] for i in face],patch,uv)

def shifted(src,fn):
    src.v=[tuple(fn(Vector(v))) for v in src.v]
    return src

def prism(g,poly,x0,x1,patch=0,bevel=0):
    """YZ profile, extruded in X; optional single bevel for arch voussoirs."""
    if len(poly)<3:return
    pts=[(x,y,z) for x in [x0,x1] for z,y in poly];n=len(poly)
    faces=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]
    faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    if bevel:
        bm=bmesh.new();vs=[bm.verts.new(v) for v in pts]
        for f in faces:bm.faces.new([vs[i] for i in f])
        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
        bmesh.ops.bevel(bm,geom=list(bm.edges),offset=bevel,segments=1,affect='EDGES')
        for f in bm.faces:g.face([tuple(v.co) for v in f.verts],patch)
        bm.free()
    else:
        for f in faces:g.face([pts[i] for i in f],patch)

def clip(poly,fn):
    out=[]
    for a,b in zip(poly,poly[1:]+poly[:1]):
        fa,fb=fn(*a),fn(*b)
        if fa>=0:out.append(a)
        if (fa>=0)!=(fb>=0):
            t=fa/(fa-fb);out.append((a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1])))
    return out

def panel(g,poly,x,sign,patch,lod):
    if len(poly)<3:return
    cy=sum(p[1] for p in poly)/len(poly);cz=sum(p[0] for p in poly)/len(poly)
    if lod==2:
        g.face([(x,y,z) for z,y in poly],patch);return
    front=[(z+(cz-z)*.09,y+(cy-y)*.11) for z,y in poly]
    for i in range(len(poly)):
        j=(i+1)%len(poly)
        g.face([(x-sign*.018,poly[i][1],poly[i][0]),(x-sign*.018,poly[j][1],poly[j][0]),
                (x+sign*.022,front[j][1],front[j][0]),(x+sign*.022,front[i][1],front[i][0])],patch)
    g.face([(x+sign*.022,y,z) for z,y in front],patch)

def slab(g,x0,x1,z0,z1,h,patch,lod):
    if lod==2:
        g.face([(x0,h(z0),z0),(x1,h(z0),z0),(x1,h(z1),z1),(x0,h(z1),z1)],patch);return
    b=.026
    outer=[(x0,z0),(x1,z0),(x1,z1),(x0,z1)]
    inner=[(x0+b,z0+b),(x1-b,z0+b),(x1-b,z1-b),(x0+b,z1-b)]
    for i in range(4):
        j=(i+1)%4
        g.face([(outer[i][0],h(outer[i][1])-.025,outer[i][1]),(outer[j][0],h(outer[j][1])-.025,outer[j][1]),
                (inner[j][0],h(inner[j][1]),inner[j][1]),(inner[i][0],h(inner[i][1]),inner[i][1])],patch)
    g.face([(x,h(z),z) for x,z in inner],patch)

def texture_material(name,file,rough=.86):
    m=w.material(name,(1,1,1),rough)
    tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(HERE/'Textures'/file))
    m.node_tree.links.new(tex.outputs['Color'],m.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
    return m

def palette_texture():
    # Low-frequency colour palette, no directional lighting baked into it.
    colors=[(.38,.23,.105),(.29,.165,.074),(.11,.13,.12),(.055,.21,.51),
            (.82,.61,.22),(.35,.42,.12),(.45,.50,.17),(.63,.55,.35),
            (.25,.35,.09),(.43,.55,.13),(.70,.68,.34),(.18,.41,.43),
            (.27,.55,.57),(.59,.75,.67),(.28,.26,.20),(.61,.58,.48)]
    size=256;pixels=[]
    for y in range(size):
        for x in range(size):
            p=(y//64)*4+x//64; c=colors[p]
            # Wood grain runs along U; other swatches softly mottled.
            t=(.022*math.sin(y*.71+2*math.sin(x*.09))+.012*math.sin(y*1.9)) if p<2 else 0
            pixels.extend([max(0,min(1,v+t)) for v in c]+[1])
    im=bpy.data.images.new('T_Bridge_Palette',width=size,height=size,alpha=False)
    im.pixels.foreach_set(pixels);im.filepath_raw=str(HERE/'Textures/T_Bridge_Palette_BaseColor.png');im.file_format='PNG';im.save()
    # Root -> tip gradient: compatible UV.y bend mask and normal texture mipmaps.
    pix=[]
    for y in range(128):
        t=y/127
        for x in range(32):pix.extend([.28+.31*t,.40+.22*t,.085+.105*t,1])
    im=bpy.data.images.new('T_Bridge_Grass',width=32,height=128,alpha=False)
    im.pixels.foreach_set(pix);im.filepath_raw=str(HERE/'Textures/T_Bridge_Grass_BaseColor.png');im.file_format='PNG';im.save()
    # One continuous terrain colour map. No per-cell colour changes or seams.
    pix=[];size=512
    for j in range(size):
        z=-8+16*j/(size-1)
        for i in range(size):
            x=-7+14*i/(size-1)
            n=.5+.22*math.sin(x*2.3+math.sin(z*1.7))+.16*math.sin(z*3.5+x)
            grass=(.35+.085*n,.43+.075*n,.12+.045*n)
            dirt=(.60+.055*n,.49+.045*n,.29+.035*n)
            wet=(.28,.28,.19)
            path=1-site.smooth(1.27,1.85,abs(x)+.065*math.sin(z*4))
            shore=1-site.smooth(3.45,4.85,abs(z)+.13*math.sin(x*2))
            mix=max(path,shore)
            color=[grass[k]*(1-mix)+dirt[k]*mix for k in range(3)]
            damp=1-site.smooth(2.75,3.9,abs(z))
            pix.extend([color[k]*(1-damp)+wet[k]*damp for k in range(3)]+[1])
    im=bpy.data.images.new('T_Bridge_Terrain',width=size,height=size,alpha=False)
    im.pixels.foreach_set(pix);im.filepath_raw=str(HERE/'Textures/T_Bridge_Terrain_BaseColor.png');im.file_format='PNG';im.save()

def colorize(g):
    for k,(f,p) in enumerate(zip(g.f,g.patches)):
        col=p%4;row=p//4
        pts=[Vector(g.v[i]) for i in f];n=(pts[1]-pts[0]).cross(pts[2]-pts[0]).normalized()
        t=(pts[1]-pts[0]).normalized();bt=n.cross(t)
        coords=[(v.dot(t),v.dot(bt)) for v in pts]
        a=min(v[0] for v in coords);b=max(v[0] for v in coords);c=min(v[1] for v in coords);d=max(v[1] for v in coords)
        g.uvs[k]=[((col+.18+.64*(u-a)/max(1e-6,b-a))/4,(row+.18+.64*(v-c)/max(1e-6,d-c))/4) for u,v in coords]
    return g

def mesh(g,name,coll,mat,palette=False):
    if palette:colorize(g)
    ob=g.mesh(name,coll,mat)
    # Open water/heightfield surfaces must face up for engine backface culling.
    if 'Water' in name or 'TerrainReference' in name:
        bm=bmesh.new();bm.from_mesh(ob.data)
        for f in bm.faces:
            if f.normal.z<0:f.normal_flip()
        bm.to_mesh(ob.data);bm.free();ob.data.update()
    ob.data.calc_loop_triangles()
    REPORT['meshes'][name]=w.audit(ob)
    return ob

def mortar(lod):
    g=G();n=[40,28,18][lod]
    # Continuous structural volume: no light through joints, real open arch.
    for i in range(n):
        a=-5.4+10.8*i/n;b=-5.4+10.8*(i+1)/n
        bottom=lambda z:-1.55+2.05*math.sqrt(max(0,1-(z/3.25)**2)) if abs(z)<3.25 else -1.72
        prism(g,[(a,bottom(a)),(b,bottom(b)),(b,site.deck_height(b)-.09),(a,site.deck_height(a)-.09)],-1.70,1.70,14)
    return g

def bridge_stone(lod):
    g=G()
    # Radial arch ring, four rows across the barrel at LOD0.
    n=[19,15,13][lod];cross=[4,2,1][lod]
    for i in range(n):
        t0=math.pi*i/n+.004;t1=math.pi*(i+1)/n-.004
        poly=[(3.25*math.cos(t0),-1.55+2.05*math.sin(t0)),
              (3.25*math.cos(t1),-1.55+2.05*math.sin(t1)),
              (3.66*math.cos(t1),-1.55+2.43*math.sin(t1)),
              (3.66*math.cos(t0),-1.55+2.43*math.sin(t0))]
        for j in range(cross):
            x0=-1.78+j*3.56/cross+.009;x1=-1.78+(j+1)*3.56/cross-.009
            prism(g,poly,x0,x1,(i+j*7)%6,.018 if lod==0 else 0)
    # Staggered masonry spandrels, neatly clipped around the stone arch ring.
    for side in [-1,1]:
        for row in range(8):
            ya=-1.72+row*.36+.009;yb=ya+.338
            cuts=[-5.4];z=-5.4+(.36 if row%2 else .72)
            while z<5.2:cuts.append(z);z+=.68+.06*math.sin(row*3+z*4)
            cuts.append(5.4)
            for col,(a,b) in enumerate(zip(cuts,cuts[1:])):
                for half in [-1,1]:
                    if half==-1 and a>=0 or half==1 and b<=0:continue
                    poly=[(a+.012,ya),(b-.012,ya),(b-.012,yb),(a+.012,yb)]
                    poly=clip(poly,lambda z,y:half*z)
                    # Ellipse outer-boundary chord through this course.
                    radius=lambda y:3.66*math.sqrt(max(0,1-((y+1.55)/2.43)**2)) if y>=-1.55 else 3.66
                    r0=radius(ya);r1=radius(yb)
                    poly=clip(poly,lambda z,y:half*z-(r0+(r1-r0)*(y-ya)/(yb-ya))-.012)
                    if not poly:continue
                    poly=clip(poly,lambda z,y:site.deck_height(z)-.13-y)
                    if len(poly)>2:panel(g,poly,side*1.76,side,(row*13+col*7)%6,lod)
    # Crown paving follows a continuous profile; fine joints cannot block walking.
    nz=[18,12,9][lod];nx=[5,4,3][lod]
    for j in range(nz):
        za=-5.4+10.8*j/nz;zb=-5.4+10.8*(j+1)/nz
        cuts=[-1.43]+[-1.43+2.86*(i+(.5 if j%2 else 0))/nx for i in range(1,nx)]+[1.43]
        for i,(a,b) in enumerate(zip(cuts,cuts[1:])):
            slab(g,a+.008,b-.008,za+.006,zb-.006,site.deck_height,(i*3+j*7)%6,lod)
    # Low parapet plinth and cap stones; no high wall hiding the deck.
    for side in [-1,1]:
        for i in range([18,12,9][lod]):
            n=[18,12,9][lod];a=-5.4+10.8*i/n;b=-5.4+10.8*(i+1)/n
            poly=[(a+.007,site.deck_height(a)-.09),(b-.007,site.deck_height(b)-.09),
                  (b-.007,site.deck_height(b)+.20),(a+.007,site.deck_height(a)+.20)]
            prism(g,poly,min(side*1.46,side*1.8),max(side*1.46,side*1.8),i%6,.015 if lod==0 else 0)
        for z in [-5.12,-2.56,0,2.56,5.12]:
            y=site.deck_height(z)
            for row in range(3 if lod<2 else 1):
                rows=3 if lod<2 else 1
                w.bevel_box(g,(side*1.64-.20,y+.20+row*.65/rows,z-.20),
                    (side*1.64+.20,y+.20+(row+1)*.65/rows-.007,z+.20),row%6,0 if lod==0 else 2,.025)
            w.bevel_box(g,(side*1.64-.25,y+.84,z-.25),(side*1.64+.25,y+.95,z+.25),1,0 if lod==0 else 2,.022)
    return g

def wood(lod):
    g=G()
    for side in [-1,1]:
        xs=side*1.64
        for a,b in zip([-5.12,-2.56,0,2.56],[-2.56,0,2.56,5.12]):
            for h in [.43,.74]:
                ya=site.deck_height(a)+h;yb=site.deck_height(b)+h
                tmp=G();w.bevel_box(tmp,(xs-.065,ya-.055,a),(xs+.065,ya+.055,b),0,0 if lod==0 else 2,.015)
                shifted(tmp,lambda p:Vector((p.x,p.y+(yb-ya)*(p.z-a)/(b-a),p.z)))
                append(g,tmp)
    # Two modest diagonal banners. No rivets, ornate bolts or busy brackets.
    for x,z in [(-1.64,-4.55),(1.64,4.55)]:
        base=site.deck_height(z)
        w.bevel_box(g,(x-.065,base+.10,z-.065),(x+.065,base+2.52,z+.065),0,0 if lod==0 else 2,.012)
        w.bevel_box(g,(x-.085,base+2.37,z-.49),(x+.085,base+2.47,z+.49),0,0 if lod==0 else 2,.01)
        for h in [.34,.91]:w.bevel_box(g,(x-.076,base+h,z-.078),(x+.076,base+h+.07,z+.078),2,2)
    return g

def banners(lod):
    cloth=G();trim=G()
    for idx,(x,z) in enumerate([(-1.64,-4.55),(1.64,4.55)]):
        base=site.deck_height(z)+2.35
        nx,ny=[(6,8),(4,5),(2,3)][lod]
        def pos(u,v,off=0):
            return (x+.075+.045*math.sin(u*math.pi*2+v*3)*v+off,base-v*(.95+.18*abs(2*u-1)),z+(u-.5)*.68)
        for j in range(ny):
            for i in range(nx):
                u=i/nx;v=j/ny;du=1/nx;dv=1/ny
                q=[pos(u,v),pos(u+du,v),pos(u+du,v+dv),pos(u,v+dv)]
                cloth.face(q,3);cloth.face(list(reversed([(a-.005,b,c) for a,b,c in q])),3)
        # Cream diamond emblem readable from a strategy camera; no tiny heraldry.
        for s in [-1,1]:
            trim.face([pos(.5,.23,s*.009),pos(.72,.42,s*.009),pos(.5,.64,s*.009),pos(.28,.42,s*.009)],4)
        for a,b in [(0,.055),(.945,1)]:
            for j in range(ny):trim.face([pos(a,j/ny,.009),pos(b,j/ny,.009),pos(b,(j+1)/ny,.009),pos(a,(j+1)/ny,.009)],4)
        # small pyramid finial
        y=base+.22
        pts=[(x-.1,y,z-.1),(x+.1,y,z-.1),(x+.1,y,z+.1),(x-.1,y,z+.1)]
        for i in range(4):trim.face([pts[i],pts[(i+1)%4],(x,y+.22,z)],4)
    return cloth,trim

def terrain(lod):
    g=G();step=[.5,1,2][lod]
    nx=round(14/step);nz=round(16/step)
    for i in range(nx):
        for j in range(nz):
            x=-7+14*i/nx;z=-8+16*j/nz
            coords=[(x,z),(x+14/nx,z),(x+14/nx,z+16/nz),(x,z+16/nz)]
            midz=z+8/nz;midx=x+7/nx
            if abs(midz)<2.8:p=14
            elif abs(midx)<1.55 and abs(midz)>4.5:p=7
            elif abs(midz)<3.65:p=7
            else:p=5+int((i*7+j*3)%5==0)
            g.face([(a,site.terrain_height(a,b),b) for a,b in coords],p,[( (a+7)/14,(b+8)/16) for a,b in coords])
    return g

def rocks(lod):
    g=G();rng=random.Random(site.SEED+22);placements=[]
    for side in [-1,1]:
        for x in [-3.8,-2.55,2.42,3.75,5.1,-5.0]:
            z=side*(3.90+rng.uniform(-.2,.30));r=rng.uniform(.28,.64)
            placements.append((x,site.terrain_height(x,z)+r*.35,z,r))
    for i in range(42):
        x=rng.uniform(-5.8,5.8);z=rng.choice([-1,1])*rng.uniform(3.75,6.3)
        if abs(x)<1.95:continue
        r=rng.uniform(.08,.22);placements.append((x,site.terrain_height(x,z)+r*.2,z,r))
    for i,(x,y,z,r) in enumerate(placements):
        if lod==2 and r<.28:continue
        bm=bmesh.new();bmesh.ops.create_icosphere(bm,subdivisions=2 if lod==0 and r>.28 else 1,radius=1)
        for v in bm.verts:
            v.co=Vector((x+v.co.x*r*(1+.14*math.sin(i+v.co.z*4)),y+v.co.y*r*.74,z+v.co.z*r*.82))
        for f in bm.faces:g.face([tuple(v.co) for v in f.verts],i%6)
        bm.free()
    return g

def grass(lod):
    g=G();rng=random.Random(site.SEED+44)
    for i in range(140):
        x=rng.uniform(-5.7,5.7);z=rng.choice([-1,1])*rng.uniform(3.9,6.4)
        if abs(x)<2.05:continue
        blades=[(rng.uniform(0,math.tau),rng.uniform(.18,.43),rng.uniform(.036,.068),rng.uniform(.10,.25)) for _ in range(6)]
        if lod==1 and i%2:continue
        if lod==2:continue
        y=site.terrain_height(x,z)+.015
        for angle,h,wide,bend in blades[:6 if lod==0 else 4]:
            dx=math.cos(angle);dz=math.sin(angle)
            pts=[]
            for t,ww in [(0,wide),(.5,wide*.72),(1,.001)]:
                cx=x+dx*bend*t*t;cz=z+dz*bend*t*t
                pts.extend([(cx-dz*ww,y+h*t,cz+dx*ww),(cx+dz*ww,y+h*t,cz-dx*ww)])
            for k in range(2):
                q=[pts[k*2],pts[k*2+1],pts[k*2+3],pts[k*2+2]]
                uv=[(0,k*.5),(1,k*.5),(1,(k+1)*.5),(0,(k+1)*.5)]
                g.face(q,0,uv);g.face(list(reversed([(a,b,c+.001) for a,b,c in q])),0,list(reversed(uv)))
    return g

def water():
    g=G()
    for i in range(28):
        a=-7+i*.5;b=a+.5;wa=site.channel_half_width(a)+.18;wb=site.channel_half_width(b)+.18
        g.face([(a,site.WATER_Y,-wa),(b,site.WATER_Y,-wb),(b,site.WATER_Y,wb),(a,site.WATER_Y,wa)],11)
    return g

def ripples():
    g=G();rng=random.Random(4411)
    for i in range(120):
        x=rng.uniform(-6.8,6.8);z=rng.uniform(-2.8,2.8)
        length=rng.uniform(.07,.35);width=rng.uniform(.012,.035);h=site.WATER_Y+.009
        g.face([(x-length,h,z),(x+length,h,z),(x+length*.8,h,z+width),(x-length*.7,h,z+width)],13 if i%4==0 else 12)
    return g

def collider():
    g=G()
    for i in range(20):
        a=-5.4+10.8*i/20;b=-5.4+10.8*(i+1)/20
        # Simple solid strips: step-free top, does not fill arch opening.
        prism(g,[(a,site.deck_height(a)-.12),(b,site.deck_height(b)-.12),
                 (b,site.deck_height(b)),(a,site.deck_height(a))],-1.44,1.44)
    return g

def export(name,objects):
    bpy.ops.object.select_all(action='DESELECT')
    for ob in objects:ob.hide_set(False);ob.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
    bpy.ops.export_scene.fbx(filepath=str(HERE/'Meshes'/f'{name}.fbx'),use_selection=True,
        object_types={'MESH','EMPTY'},axis_forward='-Z',axis_up='Y',global_scale=1,
        apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',bake_space_transform=True,
        mesh_smooth_type='FACE',use_tspace=True,add_leaf_bones=False,bake_anim=False,path_mode='RELATIVE')

def camera(pos,target,scale):
    d=bpy.data.cameras.new('Camera');ob=bpy.data.objects.new('Camera',d);studio.objects.link(ob)
    ob.location=w.B(pos);ob.rotation_euler=(w.B(target)-ob.location).to_track_quat('-Z','Y').to_euler()
    d.type='ORTHO';d.ortho_scale=scale;bpy.context.scene.camera=ob;return ob

def render(name,pos,target,scale,res=(1500,1100)):
    camera(pos,target,scale);sc=bpy.context.scene
    sc.render.resolution_x=res[0];sc.render.resolution_y=res[1];sc.render.filepath=str(HERE/'Preview'/name)
    bpy.ops.render.render(write_still=True)

def preflight():
    source=ROOT/'Source/Dependencies/Bridge_Stone_A/SM_Grass_Short_A.fbx'
    if not source.is_file():
        raise FileNotFoundError(f'Published grass preflight input missing: {source}; run git lfs pull')
    bpy.ops.import_scene.fbx(filepath=str(source))
    records=[]
    for ob in list(bpy.context.scene.objects):
        if ob.type=='MESH':
            me=ob.data;me.calc_loop_triangles();me.calc_tangents()
            uv=me.uv_layers.active
            records.append(dict(name=ob.name,vertices=len(me.vertices),triangles=len(me.loop_triangles),
                normals=all(v.normal.length>.5 for v in me.vertices),tangents=True,uv0=bool(uv),
                uv_y_range=[min(x.uv.y for x in uv.data),max(x.uv.y for x in uv.data)],
                material_slots=[m.name for m in me.materials],colors=list(me.color_attributes.keys())))
        bpy.data.objects.remove(ob,do_unlink=True)
    REPORT['foliage_preflight']=dict(source=str(source),meshes=records,
        classification='COMPATIBLE WITH MASK/AUTHORING CHANGE',
        decision='New separate grass mesh uses explicit UV0.y root=0 / mid=.5 / tip=1. No rigid stone/wood in vegetation renderer. Normal map unused. LC_Grass at integration; no shader changes.',
        unity_validator='NOT RUN; source preparation only',play_mode_close_far='NOT RUN')
    print('FOLIAGE_PREFLIGHT',json.dumps(REPORT['foliage_preflight']),flush=True)

def main():
    global studio
    for folder in ['Textures','Meshes','Preview','QA','References']:(HERE/folder).mkdir(parents=True,exist_ok=True)
    ref=HERE/'References/Bridge_Concept.png'
    if not ref.is_file():
        raise FileNotFoundError(f'Published bridge concept missing: {ref}')
    shutil.copy2(ROOT/'Source/Architecture/Wall_Stone_Modular/v002/Textures/T_WallStoneSurface_A_BaseColor.png',HERE/'Textures/T_WallStoneSurface_A_BaseColor.png')
    bpy.ops.wm.read_factory_settings(use_empty=True)
    preflight();palette_texture()
    stone=texture_material('M_Bridge_Stone','T_WallStoneSurface_A_BaseColor.png')
    palette=texture_material('M_Bridge_Palette','T_Bridge_Palette_BaseColor.png')
    vegetation=texture_material('M_Bridge_Grass','T_Bridge_Grass_BaseColor.png')
    terrain_mat=texture_material('M_Bridge_TerrainReference','T_Bridge_Terrain_BaseColor.png')
    flag=w.material('M_Bridge_FactionCloth',(.035,.16,.48),.9)
    sc=bpy.context.scene;sc.unit_settings.system='METRIC';sc.unit_settings.scale_length=1
    for lod in range(3):
        coll=w.collection(f'Bridge_Module_LOD{lod}');LODS.append(coll)
        obs=[]
        obs.append(mesh(bridge_stone(lod),f'SM_Bridge_Stone_LOD{lod}',coll,stone))
        obs.append(mesh(mortar(lod),f'SM_Bridge_Mortar_LOD{lod}',coll,palette,True))
        obs.append(mesh(wood(lod),f'SM_Bridge_Wood_LOD{lod}',coll,palette,True))
        cloth,trim=banners(lod)
        obs.append(mesh(cloth,f'SM_Bridge_FactionCloth_LOD{lod}',coll,flag))
        obs.append(mesh(trim,f'SM_Bridge_Trim_LOD{lod}',coll,palette,True))
        export(f'SM_Bridge_Stone_A_LOD{lod}',obs)
        dressing=[mesh(rocks(lod),f'SM_Bridge_Rocks_LOD{lod}',coll,stone)]
        if lod<2:dressing.append(mesh(grass(lod),f'SM_Bridge_Grass_LOD{lod}',coll,vegetation))
        export(f'SM_Bridge_Dressing_A_LOD{lod}',dressing)
        terrain_ob=mesh(terrain(lod),f'SM_Bridge_TerrainReference_LOD{lod}',coll,terrain_mat)
        for poly in terrain_ob.data.polygons:poly.use_smooth=True
        export(f'SM_Bridge_TerrainReference_LOD{lod}',[terrain_ob])
        if lod:coll.hide_render=True;coll.hide_viewport=True
    support=w.collection('Support_Water_Sockets_Collision')
    water_ob=mesh(water(),'SM_Bridge_Water',support,palette,True)
    ripple_ob=mesh(ripples(),'SM_Bridge_WaterAccents',support,palette,True)
    export('SM_Bridge_Water_A',[water_ob,ripple_ob])
    c=mesh(collider(),'COL_Bridge_Deck',support,stone)
    blockers=[]
    for side in [-1,1]:
        g=G()
        for a,b in zip([-5.4,-2.7,0,2.7],[-2.7,0,2.7,5.4]):
            prism(g,[(a,site.deck_height(a)),(b,site.deck_height(b)),(b,site.deck_height(b)+.9),(a,site.deck_height(a)+.9)],min(side*1.43,side*1.85),max(side*1.43,side*1.85))
        blockers.append(mesh(g,'COL_Bridge_Rail_'+str(side),support,stone))
    export('COL_Bridge_A',[c]+blockers)
    for ob in [c]+blockers:ob.hide_render=True;ob.hide_set(True);ob.display_type='WIRE'
    sockets=[]
    for entry in site.contract()['road_sockets']+site.contract()['river_sockets']:
        ob=bpy.data.objects.new(entry['id'],None);support.objects.link(ob);ob.location=w.B(entry['position']);ob.empty_display_size=.4
        ob['outward_unity']=entry['outward'];sockets.append(ob)
    export('Bridge_Sockets',sockets)
    studio=w.collection('Studio_PreviewOnly')
    ground=w.material('Studio_Sand',(.32,.30,.245),1)
    g=G();g.box((-200,-2.11,-200),(200,-2.1,200));g.mesh('StudioFloor',studio,ground)
    sc.world=bpy.data.worlds.new('BridgeWorld');sc.world.use_nodes=True
    sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.67,.76,.88,1)
    sc.world.node_tree.nodes['Background'].inputs[1].default_value=.45
    light=bpy.data.lights.new('Sun','SUN');light.energy=3;light.color=(1,.92,.80);light.angle=math.radians(14)
    sun=bpy.data.objects.new('Sun',light);studio.objects.link(sun);sun.rotation_euler=(math.radians(27),math.radians(-24),math.radians(-32))
    sc.render.engine='CYCLES';sc.cycles.samples=32;sc.cycles.use_denoising=True
    sc.render.image_settings.file_format='PNG';sc.render.resolution_percentage=100
    sc.view_settings.view_transform='AgX'
    sc.view_settings.exposure=.65
    bpy.context.preferences.filepaths.save_version=0
    camera((15,11,-12),(0,-.15,0),19)
    for im in bpy.data.images:
        if im.source=='FILE':im.pack()
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':
                area.spaces.active.region_3d.view_perspective='CAMERA'
                area.spaces.active.shading.type='MATERIAL'
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'Bridge_Stone_A.blend'))
    (HERE/'bridge-site.json').write_text(json.dumps(site.contract(),indent=2),encoding='utf-8')
    (HERE/'QA/geometry_report.json').write_text(json.dumps(REPORT,indent=2),encoding='utf-8')
    render('Bridge_Hero.png',(15,11,-12),(0,-.15,0),20.5)
    if '--quick' not in sys.argv:
        render('Bridge_Reverse.png',(-15,9,11),(0,-.1,0),18)
        render('Bridge_Side.png',(18,4,0),(0,.15,0),15,(1600,900))
        render('Bridge_Top.png',(0,24,.001),(0,0,0),18,(1300,1300))
        render('Bridge_Detail.png',(6,4,-5),(0,.35,-.6),9,(1400,1100))
        # Honest real-time raster check: sunlight + ambient only, no path tracing.
        sc.render.engine='BLENDER_EEVEE_NEXT'
        render('Bridge_Realtime_Eevee.png',(15,11,-12),(0,-.15,0),20.5)
    print('BRIDGE_BUILD_COMPLETE',json.dumps({k:v['triangles'] for k,v in REPORT['meshes'].items()}),flush=True)

if __name__=='__main__':main()
