"""Blender 4.4: approved v002 walls + archer tower, gate and customizable pennant.
Local authoring only. Unity coordinates in functions; exports Y-up metres.
"""
import sys, math, json, shutil, hashlib, random
from pathlib import Path
import bpy
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
import wall_geometry as w

HERE=Path(__file__).resolve().parent
PREVIOUS=HERE.parent/'v002'
ROOT=HERE.parents[3]
WORK=ROOT.parent
G=w.Geometry
TOWER='SM_ArcherTower_A'
GATE='SM_Wall_Gatehouse_A'
LEFT='SM_Wall_GateLeaf_Left_A'
RIGHT='SM_Wall_GateLeaf_Right_A'
TRIM='SM_Wall_Banner_Trim_A'
ASSETS={}
CONTRACT={'version':'v003','unity_tested':False,'coordinates':'metres, Y-up, wall axis Z',
          'assets':{},'source_wall_version':'v002 approved by user 2026-10-03'}

def prepare():
    for folder in ['Meshes','Textures','References','Preview','QA']:(HERE/folder).mkdir(exist_ok=True)
    for name in ['T_WallStoneSurface_A_BaseColor.png','generation-prompt.txt']:
        shutil.copy2(PREVIOUS/'Textures'/name,HERE/'Textures'/name)
    for sub,name in [('RoofTile','RoofTile_BaseColor.png'),('DoorWood','DoorWood_A_BaseColor.png')]:
        shutil.copy2(WORK/'CozySettlement/Mat'/sub/name,HERE/'Textures'/name)
    ref=Path('C:/Users/AACE~1/AppData/Local/Temp/codex-clipboard-11d45fd4-658e-4d7f-bf4d-f4e083ea08fa.png')
    if ref.exists():shutil.copy2(ref,HERE/'References/ArcherTower_Concept.png')
    shutil.copy2(PREVIOUS/'References/Wall_Concept.png',HERE/'References/Wall_Concept.png')

def textured(name,file,rough=.9):
    m=w.material(name,(1,1,1),rough)
    tex=m.node_tree.nodes.new('ShaderNodeTexImage')
    tex.image=bpy.data.images.load(str(HERE/'Textures'/file));tex.image.colorspace_settings.name='sRGB'
    m.node_tree.links.new(tex.outputs['Color'],m.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
    return m

def pennant_point(u,t):
    # The upper edge is fixed; gently draped cloth remains safely in front of stone.
    if t>.8:
        q=(t-.8)/.2
        tip=Vector((0,-.60,.014+.011*math.sin(.3)+.006))
        if q>1-1e-6:return tuple(tip)
        base=Vector(pennant_point(.5+(u-.5)/(1-q),.8))
        return tuple(base*(1-q)+tip*q)
    return ((u-.5)*.36,-t*.60,.014+.011*math.sin(u*math.pi*4+.3)*math.sin(t*math.pi/2)+.006*t)

def pennant(lod,coll,mat):
    nx,ny=[(8,10),(4,5),(2,2)][lod];g=G()
    for side in [0,1]:
        def face(uvs):
            points=[Vector(pennant_point(u,t))+Vector((0,0,-.001*side)) for u,t in uvs]
            tex=[(u if side==0 else 1-u,1-t) for u,t in uvs]
            if side:points.reverse();tex.reverse()
            g.face(points,uv=tex)
        for j in range(ny):
            a=.8*j/ny;b=.8*(j+1)/ny
            for i in range(nx):face([(i/nx,a),((i+1)/nx,a),((i+1)/nx,b),(i/nx,b)])
        for i in range(nx):face([(i/nx,.8),((i+1)/nx,.8),(.5,1)])
    ob=g.mesh(w.NAMES[4]+'_LOD'+str(lod),coll,mat)
    for p in ob.data.polygons:p.use_smooth=True
    wind=ob.data.color_attributes.new(name='WindMask',type='FLOAT_COLOR',domain='POINT')
    for v,c in zip(ob.data.vertices,wind.data):c.color=(min(1,max(0,-w.U(v.co)[1]/.60))**1.7,0,0,1)
    return ob

def pennant_trim(lod):
    g=G();outer=[(0,0),(1,0),(1,.8),(.5,1),(0,.8)]
    inner=[(.035,.022),(.965,.022),(.965,.789),(.5,.960),(.035,.789)]
    cuts=[6,3,1][lod]
    for side in [0,1]:
        for i in range(5):
            j=(i+1)%5
            for k in range(cuts):
                a=k/cuts;b=(k+1)/cuts
                coords=[]
                for p,q,t in [(outer[i],outer[j],a),(outer[i],outer[j],b),(inner[i],inner[j],b),(inner[i],inner[j],a)]:
                    u=p[0]+(q[0]-p[0])*t;v=p[1]+(q[1]-p[1])*t
                    pos=Vector(pennant_point(u,v));pos.z+=.004 if side==0 else -.005;coords.append(pos)
                if side:coords.reverse()
                g.face(coords)
    return g

def support(lod):
    g=G()
    detail=0 if lod==0 else 2
    for x in [-.15,.15]:
        w.bevel_box(g,(x-.018,-.03,0),(x+.018,.025,.015),0,detail,.004)
        if lod<2:w.bevel_box(g,(x-.009,-.005,.008),(x+.009,.012,.058),0,detail,.003)
    w.bevel_box(g,(-.205,0,.044),(.205,.018,.062),0,detail,.004)
    # Two hanging loops, visually connected to rod and cloth.
    for x in [-.132,.132]:w.bevel_box(g,(x-.008,-.033,.024),(x+.008,.016,.053),0,detail,.002)
    if lod==0:
        for x in [-.210,.210]:w.bevel_box(g,(x-.010,-.002,.040),(x+.010,.021,.065),0,0,.005)
    return g

def transform(g,fn):
    g.v=[tuple(fn(Vector(p))) for p in g.v];return g

def append(dst,src):
    for f,p,uv in zip(src.f,src.patches,src.uvs):dst.face([src.v[i] for i in f],p,uv)

def slab(g,lo,hi,lod,seed=0):
    if lod==0:w.rock(g,lo,hi,seed,1,.026)
    elif lod==1:g.box(lo,hi,seed)
    else:g.box(lo,hi,seed)

def tower_stone(lod):
    g=G()
    # Thin outer stone courses over a cheap closed core; no modelled interior.
    g.box((-.78,.08,-.78),(.78,2.64,.78))
    w.bevel_box(g,(-1.0,0,-1.0),(1.0,.18,1.0),0,lod,.028)
    w.bevel_box(g,(-.96,.18,-.96),(.96,.34,.96),1,lod,.022)
    levels=[.34,.59,.85,1.11,1.37,1.63,1.84,2.10,2.36,2.61]
    for side in range(4):
        angle=side*math.pi/2;c=math.cos(angle);s=math.sin(angle)
        for row,(ya,yb) in enumerate(zip(levels,levels[1:])):
            cuts=[-.90,-.48,-.06,.40,.90] if row%2==0 else [-.90,-.68,-.23,.22,.67,.90]
            if row in [6,7]:cuts=sorted(set(cuts+[-.067,.067]))
            for k,(a,b) in enumerate(zip(cuts,cuts[1:])):
                if row in [6,7] and a>=-.067 and b<=.067:continue
                tmp=G()
                if lod==2:
                    tmp.face([(.90,ya+.003,a+.004),(.90,ya+.003,b-.004),(.90,yb-.003,b-.004),(.90,yb-.003,a+.004)],side*53+row*7+k)
                else:slab(tmp,(.78,ya+.003,a+.004),(.90,yb-.003,b-.004),lod,side*53+row*7+k)
                append(g,transform(tmp,lambda p:Vector((c*p.x+s*p.z,p.y,-s*p.x+c*p.z))))
    w.bevel_box(g,(-.94,2.60,-.94),(.94,2.70,.94),3,lod,.02)
    return g

def tower_wood(lod):
    g=G()
    for side in range(4):
        a=side*math.pi/2;c=math.cos(a);s=math.sin(a)
        t=G();w.bevel_box(t,(.87,2.63,-1.08),(1.05,2.76,1.08),0,lod,.012)
        for z in [-.72,0,.72]:w.bevel_box(t,(.85,2.43,z-.07),(1.10,2.71,z+.07),1,lod,.012)
        # Dark shallow recess behind real slit opening, same dark timber material.
        t.box((.781,1.83,-.070),(.784,2.37,.070))
        append(g,transform(t,lambda p:Vector((c*p.x+s*p.z,p.y,-s*p.x+c*p.z))))
    return g

def roof(lod):
    g=G();base=2.72;rise=.73
    # Continuous under-roof avoids light leaking through tile joints.
    for i in range(4):
        a=i*math.pi/2;c=math.cos(a);s=math.sin(a)
        g.face([(c*1.2+s*-1.2,base,-s*1.2+c*-1.2),(c*1.2+s*1.2,base,-s*1.2+c*1.2),(0,base+rise,0)],uv=[(.3,.3),(.7,.3),(.5,.7)])
    # Four hipped sides; individual low-poly overlapping tiles at near/medium LOD.
    rows=[7,4,2][lod]
    for side in range(4):
        ang=side*math.pi/2;c=math.cos(ang);s=math.sin(ang)
        for row in range(rows):
            t0=row/rows;t1=min(1,(row+1)/rows+.025)
            a=1.20*(1-t0);b=1.20*(1-t1)
            n=max(1,round((a+b)/[.23,.42,.8][lod]))
            for col in range(n):
                p0=-1+2*col/n;p1=-1+2*(col+1)/n
                gap=.008 if n>1 else 0
                points=[(a,base+rise*t0,p0*a+gap),(a,base+rise*t0,p1*a-gap),
                        (b,base+rise*t1,p1*b),(b,base+rise*t1,p0*b)]
                if b<.0001:points=points[:2]+[(0,base+rise,0)]
                lift=.024+.012*(row%2)
                top=[Vector((c*x+s*z,y+lift,-s*x+c*z)) for x,y,z in points]
                uv=[(.23+col*.037%0.4,.24),(.40+col*.037%0.4,.24),(.39+col*.037%0.4,.70),(.23+col*.037%0.4,.70)][:len(top)]
                if lod==0 and len(top)==4:
                    mid0=(top[0]+top[1])*.5+Vector((0,.014,0));mid1=(top[2]+top[3])*.5+Vector((0,.014,0))
                    g.face([top[0],mid0,mid1,top[3]],uv=[(.3,.3),(.4,.3),(.4,.7),(.3,.7)])
                    g.face([mid0,top[1],top[2],mid1],uv=[(.4,.3),(.5,.3),(.5,.7),(.4,.7)])
                else:g.face(top,uv=uv)
                if lod<2:
                    for i in range(len(top)):
                        j=(i+1)%len(top)
                        g.face([top[i],top[j],top[j]-Vector((0,.035,0)),top[i]-Vector((0,.035,0))],uv=[(.3,.3),(.6,.3),(.6,.34),(.3,.34)])
        # Hip ridge as one narrow prism per side with stepped terracotta covers.
        if lod<2:
            for j in range(rows):
                ta=j/rows;tb=(j+1)/rows
                def p(t,off):
                    d=1.19*(1-t);x=d+off*.5;z=d-off*.5
                    return (c*x+s*z,base+rise*t+.056,-s*x+c*z)
                g.face([p(ta,-.035),p(ta,.035),p(tb,.035),p(tb,-.035)],uv=[(.3,.3),(.4,.3),(.4,.7),(.3,.7)])
    # Finial: compact cap, no expensive small decoration.
    for i in range(4):
        a=i*math.pi/2;b=(i+1)*math.pi/2
        g.face([(.065*math.cos(a),3.46,.065*math.sin(a)),(.065*math.cos(b),3.46,.065*math.sin(b)),(0,3.60,0)],uv=[(.3,.3),(.5,.3),(.4,.6)])
    return g

def prism(g,polygon,xa,xb,patch=0):
    # Polygon in Z,Y, extruded along X. Concave polygons supported by mesh triangulation.
    front=[(xb,y,z) for z,y in polygon];back=[(xa,y,z) for z,y in polygon]
    g.face(front,patch);g.face(list(reversed(back)),patch)
    for i in range(len(front)):
        j=(i+1)%len(front);g.face([back[i],back[j],front[j],front[i]],patch)

def gate_stone(lod):
    g=G();r=1.05;cy=1.23;outer=1.32
    # Twin piers with full-depth blocks. No collider/solid core across doorway.
    for sign in [-1,1]:
        for row in range(9):
            ya=row*.275;yb=ya+.275
            cut=[1.05,1.52,1.99] if row%2 else [1.05,1.32,1.72,1.99]
            if yb>cy:cut=sorted(set(cut+[outer]))
            for k,(a,b) in enumerate(zip(cut,cut[1:])):
                if a<outer and ya>=cy:continue
                top=min(yb,cy) if a<outer else yb
                za,zb=sorted([sign*a,sign*b]);slab(g,(-.47,ya+.003,za+.004),(.47,top-.003,zb-.004),lod,row*13+k)
        # Solid recessed backing in each pier, never across the passage.
        z0,z1=sorted([sign*1.33,sign*1.98]);g.box((-.43,0,z0),(.43,2.63,z1))
        w.bevel_box(g,(-.53,0,sign*1.52-.52),(.53,.14,sign*1.52+.52),1,lod,.022)
    # Voussoirs are true wedge-shaped blocks, not a texture of an arch.
    n=[15,11,9][lod]
    for i in range(n):
        a=math.pi*i/n+.005;b=math.pi*(i+1)/n-.005
        poly=[(r*math.cos(a),cy+r*math.sin(a)),(outer*math.cos(a),cy+outer*math.sin(a)),
              (outer*math.cos(b),cy+outer*math.sin(b)),(r*math.cos(b),cy+r*math.sin(b))]
        prism(g,poly,-.49,.49,i)
    # Fill spandrels above outer arch, without obstructing opening.
    for i in range(n):
        a=math.pi*i/n;b=math.pi*(i+1)/n
        za=outer*math.cos(a);zb=outer*math.cos(b);ya=cy+outer*math.sin(a);yb=cy+outer*math.sin(b)
        prism(g,[(za,ya),(za,2.62),(zb,2.62),(zb,yb)],-.45,.45,i)
    for k in range(8):
        z=-2.04+k*.51;w.bevel_box(g,(-.53,2.61,z),(.53,2.75,z+.51),k,lod,.018)
    for z in [-1.76,-.88,0,.88,1.76]:
        w.bevel_box(g,(-.45,2.75,z-.22),(.45,2.97,z+.22),2,lod,.024)
        w.bevel_box(g,(-.49,2.97,z-.24),(.49,3.04,z+.24),1,lod,.014)
    return g

def door(lod,side):
    wood=G();metal=G();n=[6,4,2][lod]
    # Hinge origin at outer edge; both leaves rotate around local Y.
    for i in range(n):
        a=.012+i*1.018/n;b=.012+(i+1)*1.018/n-.005
        def top(d):
            z=1.04-d
            return 1.23+math.sqrt(max(0,1.05**2-z*z))-.035
        poly=[(side*a,.04),(side*b,.04),(side*b,top(b)),(side*a,top(a))]
        prism(wood,poly,-.055,.055,i)
    for y in [.32,1.03,1.57]:
        a,b=sorted([side*.035,side*.99]);w.bevel_box(metal,(.059,y-.031,a),(.085,y+.031,b),0,lod,.008)
        if lod==0:
            for d in [.10,.43,.82]:w.bevel_box(metal,(.084,y-.013,side*d-.012),(.099,y+.013,side*d+.012),0,1,.004)
    # Raised central handle and hinge straps, cheap geometry.
    d=side*.84
    w.bevel_box(metal,(.075,.77,d-.03),(.10,.95,d+.03),0,lod,.008)
    for y in [.34,1.46]:w.bevel_box(metal,(-.075,y-.055,-.037),(.075,y+.055,.037),0,lod,.009)
    return wood,metal

def add_asset(name,builders,mats,extras=()):
    coll=w.collection(name);root=bpy.data.objects.new(name,None);coll.objects.link(root)
    root['authoring_contract']='Y up in FBX; local +Z wall length; root identity'
    levels=[];flat=[]
    for lod in range(3):
        parts=[]
        for part,fn in builders.items():
            ob=fn(lod).mesh(name+'_'+part+'_LOD'+str(lod),coll,mats[part]);ob.parent=root
            ob['lod_level']=lod;parts.append(ob);flat.append(ob)
        levels.append(parts)
    ASSETS[name]={'root':root,'collection':coll,'levels':levels,'lods':flat,'extras':[]}
    return ASSETS[name]

def locator(a,name,pos,yaw=0,scale=(1,1,1)):
    ob=bpy.data.objects.new(a['root'].name+'__'+name,None);a['collection'].objects.link(ob);ob.parent=a['root']
    ob.location=w.B(pos);ob.rotation_euler=(0,0,math.radians(yaw));ob.scale=scale
    ob['export_name']=name;ob.empty_display_type='ARROWS';ob.empty_display_size=.12;a['extras'].append(ob)
    return ob

def proxy(a,label,lo,hi):
    g=G();g.box(lo,hi);ob=g.mesh('UCX_'+a['root'].name+'_'+label,a['collection'],STONE)
    ob.parent=a['root'];ob.hide_render=True;ob.display_type='WIRE';ob['unity_note']='BoxCollider reference; do not render'
    a['extras'].append(ob)

def build():
    global STONE,WOOD,IRON,ROOF,TRIMMAT
    w.cloth=pennant;w.bracket=support;w.build_assets()
    STONE=bpy.data.materials['M_Wall_Stone_Shared'];IRON=bpy.data.materials['M_BannerBracket_Shared']
    WOOD=textured('M_FortificationTimber_Shared','DoorWood_A_BaseColor.png')
    ROOF=textured('M_FortificationRoof_Shared','RoofTile_BaseColor.png')
    nodes=ROOF.node_tree.nodes;links=ROOF.node_tree.links
    tex=next(n for n in nodes if n.type=='TEX_IMAGE');mix=nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY'
    mix.inputs[0].default_value=1;mix.inputs[2].default_value=(.58,.30,.15,1)
    links.new(tex.outputs['Color'],mix.inputs[1]);links.new(mix.outputs[0],nodes.get('Principled BSDF').inputs['Base Color'])
    TRIMMAT=w.material('M_PlayerBannerTrim',(1,1,1),.82)
    for name,a in w.ASSETS.items():a['levels']=[[ob] for ob in a['lods']];ASSETS[name]=a
    trim=add_asset(TRIM,{'Trim':pennant_trim},{'Trim':TRIMMAT})
    for ob in trim['lods']:
        wind=ob.data.color_attributes.new(name='WindMask',type='FLOAT_COLOR',domain='POINT')
        for v,c in zip(ob.data.vertices,wind.data):c.color=(min(1,max(0,-w.U(v.co)[1]/.60))**1.7,0,0,1)
    # Slit backs share the timber draw call and sample its darkest seam region.
    a=add_asset(TOWER,{'Stone':tower_stone,'Timber':tower_wood,'Roof':roof},{'Stone':STONE,'Timber':WOOD,'Roof':ROOF})
    for name,z,yaw in [('WallConnection_A',-.90,180),('WallConnection_B',.90,0)]:locator(a,name,(0,0,z),yaw)
    for sign,label in [(1,'XPlus'),(-1,'XMinus')]:locator(a,'BannerAnchor_'+label,(sign*.925,1.83,0),sign*90,(1.5,1.5,1.5))
    for yaw,label in [(90,'XPlus'),(-90,'XMinus'),(0,'ZPlus'),(180,'ZMinus')]:
        r=math.radians(yaw);locator(a,'ArrowOrigin_'+label,(.92*math.sin(r),2.12,.92*math.cos(r)),yaw)
    proxy(a,'Base',(-1,0,-1),(1,.34,1));proxy(a,'Shaft',(-.90,.34,-.90),(.90,2.7,.90))
    a=add_asset(GATE,{'Stone':gate_stone},{'Stone':STONE})
    locator(a,'WallConnection_Left',(0,0,-1.99),180);locator(a,'WallConnection_Right',(0,0,1.99),0)
    locator(a,'GateHinge_Left',(0,0,-1.04));locator(a,'GateHinge_Right',(0,0,1.04))
    for z,label in [(-1.56,'Left'),(1.56,'Right')]:locator(a,'BannerAnchor_'+label,(.50,2.10,z),90)
    proxy(a,'LeftPier',(-.47,0,-1.99),(.47,2.62,-1.05));proxy(a,'RightPier',(-.47,0,1.05),(.47,2.62,1.99))
    proxy(a,'Lintel',(-.47,2.29,-1.05),(.47,2.75,1.05))
    # Stepped simple arch colliders follow shoulders but keep a real opening.
    for sign in [-1,1]:
        for i,(za,zb,y) in enumerate([(.80,1.05,1.92),(.52,.80,2.14)]):
            z0,z1=sorted([sign*za,sign*zb]);proxy(a,'Arch'+str(sign)+'_'+str(i),(-.47,y,z0),(.47,2.30,z1))
    for name,sign in [(LEFT,1),(RIGHT,-1)]:
        a=add_asset(name,{'Timber':lambda l,s=sign:door(l,s)[0],'Iron':lambda l,s=sign:door(l,s)[1]}, {'Timber':WOOD,'Iron':IRON})
        z0,z1=sorted([0,sign*1.035]);proxy(a,'Leaf',(-.055,.04,z0),(.055,2.27,z1))
    # Keep exact approved stone wall geometries, adding only unambiguous locators.
    for name,length in [(w.NAMES[0],2),(w.NAMES[1],1)]:
        locator(ASSETS[name],'WallConnection_Left',(0,0,-length/2),180)
        locator(ASSETS[name],'WallConnection_Right',(0,0,length/2),0)
    # Stable, upright grain rather than accidental projection rotation.
    for name,a in ASSETS.items():
        for ob in a['lods']:
            if ob.data.materials[0]!=WOOD:continue
            uv=ob.data.uv_layers.active
            for p in ob.data.polygons:
                if name==TOWER and max(w.U(ob.data.vertices[i].co)[1] for i in p.vertices)<2.40:
                    coords=[uv.data[li].uv.copy() for li in p.loop_indices]
                    lo=[min(v[i] for v in coords) for i in [0,1]];hi=[max(v[i] for v in coords) for i in [0,1]]
                    for li,q in zip(p.loop_indices,coords):uv.data[li].uv=(.14+.001*(q.x-lo[0])/max(1e-8,hi[0]-lo[0]),.3+.2*(q.y-lo[1])/max(1e-8,hi[1]-lo[1]))
                    continue
                if abs(w.U(p.normal)[0])<.99:continue
                for li in p.loop_indices:
                    v=w.U(ob.data.vertices[ob.data.loops[li].vertex_index].co)
                    uv.data[li].uv=(v[2]*.50+.43,v[1]*.50)
    bpy.context.view_layer.update()

def instance(name,pos=(0,0,0),yaw=0,lod=0,scale=1,mat=None):
    obs=[]
    for src in ASSETS[name]['levels'][lod]:
        ob=src.copy();ob.data=src.data if mat is None else src.data.copy();w.STUDIO.objects.link(ob)
        ob.parent=None;ob.location=w.B(pos);ob.rotation_euler=(0,0,math.radians(yaw));ob.scale=(scale,)*3
        if mat:ob.data.materials.clear();ob.data.materials.append(mat)
        obs.append(ob)
    return obs

def banner(pos,yaw,scale=1,col=None,trim=None,lod=0):
    instance(w.NAMES[4],pos,yaw,lod,scale,col)
    instance(w.NAMES[5],pos,yaw,lod,scale)
    instance(TRIM,pos,yaw,lod,scale,trim)

def emblem(pos,yaw,scale=1,mat=None):
    # Preview-only heraldic lozenge. No emblem is baked into exported fabric.
    g=G();polys=[[(.50,.23),(.60,.40),(.50,.63),(.40,.40)],
                [(.30,.36),(.41,.40),(.46,.52),(.36,.48)],[(.70,.36),(.59,.40),(.54,.52),(.64,.48)]]
    for poly in polys:
        pts=[]
        for u,t in poly:p=Vector(pennant_point(u,t));p.z+=.0028;pts.append(p)
        g.face(pts)
    ob=g.mesh('QA_Optional_Heraldry_Not_Exported',w.STUDIO,mat)
    ob.location=w.B(pos);ob.rotation_euler=(0,0,math.radians(yaw));ob.scale=(scale,)*3

def preview():
    for a in ASSETS.values():a['collection'].hide_render=True
    blue=w.material('QA_FabricBlue',(.025,.105,.22),.96);gold=w.material('QA_TrimGold',(.60,.34,.07),.8)
    red=w.material('QA_FabricRed',(.33,.025,.025),.96);green=w.material('QA_FabricGreen',(.045,.21,.10),.96)
    def tower(pos=(0,0,0),yaw=0,lod=0):
        instance(TOWER,pos,yaw,lod)
        a=math.radians(yaw);bp=Vector(pos)+Vector((.925*math.cos(a),1.83,-.925*math.sin(a)))
        banner(bp,yaw+90,1.5,blue,gold,lod);emblem(bp,yaw+90,1.5,gold)
    def gate(opened=False):
        instance(GATE)
        instance(LEFT,(0,0,-1.04),90 if opened else 0)
        instance(RIGHT,(0,0,1.04),-90 if opened else 0)
        for z in [-1.56,1.56]:banner((.50,2.10,z),90,1,blue,gold);emblem((.50,2.10,z),90,1,gold)
    w.reset_studio();tower()
    for z in [-3.74,-1.82,1.82,3.74]:instance(w.NAMES[0],(0,0,z))
    w.render('ArcherTower_Joined.png',(7,4.5,-7),(0,1.4,0),10,(1700,1100))
    w.reset_studio();tower()
    w.render('ArcherTower_Closeup.png',(5,3.6,-4),(0,1.65,0),4.6,(1200,1400))
    w.reset_studio();gate()
    for z in [-2.91,2.91]:instance(w.NAMES[0],(0,0,z))
    w.render('Gate_Closed.png',(7,4.1,-4),(0,1.2,0),8,(1600,1050))
    w.reset_studio();gate(True)
    w.render('Gate_Open.png',(6,3.3,-3),(0,1.2,0),5.8,(1400,1000))
    w.reset_studio();instance(w.NAMES[0]);instance(w.NAMES[2],(0,0,1.28))
    banner((.36,1.38,1.28),90,1,blue,gold);emblem((.36,1.38,1.28),90,1,gold)
    w.render('Wall_Approved_NewBanner.png',(4,2.6,-2),(0,.8,.55),3.8,(1300,1100))
    w.reset_studio()
    for z,col,trim in [(-1.0,blue,gold),(0,red,gold),(1.0,green,bpy.data.materials['M_PlayerBannerTrim'])]:
        instance(w.NAMES[2],(0,0,z));banner((.36,1.38,z),90,1,col,trim);emblem((.36,1.38,z),90,1,trim)
    w.render('Banner_Customization.png',(5,2.5,-1.3),(0,.8,0),4,(1400,1000))
    w.reset_studio()
    for i in range(3):tower((0,0,(i-1)*3.0),0,i)
    w.render('Tower_LODs.png',(9,6,-7),(0,1.4,0),12,(1700,950))
    # Tower retrofit and gentle turn away from the exact socket. Rigid pieces.
    w.reset_studio();tower()
    start=Vector((0,0,.90))
    for yaw in [0,5,10,15,20]:
        d=Vector((math.sin(math.radians(yaw)),0,math.cos(math.radians(yaw))))
        center=start+d*.92;instance(w.NAMES[0],center,yaw);start=center+d*1.00
    for z in [-1.82,-3.74]:instance(w.NAMES[0],(0,0,z))
    w.render('Socket_Curve_Assembly.png',(11,9,-9),(0,1,2.2),14,(1700,1050))

def export_report():
    w.ASSETS.clear();w.ASSETS.update(ASSETS);w.export_all()
    for name,a in ASSETS.items():
        levels=[]
        for obs in a['levels']:
            levels.append({'triangles':sum(w.audit(ob)['triangles'] for ob in obs),
                           'renderers':len(obs),'parts':[w.audit(ob) | {'name':ob.name} for ob in obs]})
        assert all(levels[i]['triangles']>levels[i+1]['triangles'] for i in [0,1]),(name,[l['triangles'] for l in levels])
        CONTRACT['assets'][name]={'lods':levels,'locators':[
            {'name':ob['export_name'],'position':w.U(ob.location),'yaw':math.degrees(ob.rotation_euler.z),
             'scale':list(ob.scale)} for ob in a['extras'] if ob.type=='EMPTY'],
            'colliders':[w.bounds(ob) for ob in a['extras'] if ob.type=='MESH']}

if __name__=='__main__':
    prepare();bpy.ops.wm.read_factory_settings(use_empty=True)
    sc=bpy.context.scene;sc.unit_settings.system='METRIC';sc.unit_settings.scale_length=1
    sc.render.engine='CYCLES';sc.cycles.samples=24;sc.cycles.use_denoising=True
    sc.render.image_settings.file_format='PNG';sc.render.resolution_percentage=100;sc.view_settings.view_transform='AgX'
    build();export_report();w.STUDIO=w.collection('90_PREVIEW_ONLY_DO_NOT_EXPORT');preview()
    w.reset_studio();instance(TOWER,(0,0,-3));instance(GATE,(0,0,1));instance(LEFT,(0,0,-.04));instance(RIGHT,(0,0,2.04))
    instance(w.NAMES[0],(0,0,4.1));w.camera((10,7,-6),(0,1.5,.3),10)
    for a in ASSETS.values():
        for ob in [a['root']]+a['lods']+a['extras']:ob.hide_set(True)
    bpy.ops.object.select_all(action='DESELECT')
    for im in bpy.data.images:
        if im.source=='FILE':im.pack()
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'Wall_Fortifications.blend'))
    CONTRACT['source_sha256']=hashlib.sha256((HERE/'Wall_Fortifications.blend').read_bytes()).hexdigest()
    (HERE/'QA/geometry_report.json').write_text(json.dumps(CONTRACT,indent=2),encoding='utf-8')
    print('FORTIFICATIONS_COMPLETE',json.dumps({n:[l['triangles'] for l in a['lods']] for n,a in CONTRACT['assets'].items()}),flush=True)
