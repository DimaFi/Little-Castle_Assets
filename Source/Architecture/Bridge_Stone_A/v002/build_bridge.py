"""Visual redesign, immutable v001 preserved. Blender 4.4, Z-up source / Y-up FBX."""
import bpy,bmesh,math,random,json,sys,shutil,importlib.util
from array import array
from pathlib import Path
from mathutils import Vector
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import bridge_contract as site
spec=importlib.util.spec_from_file_location('bridge_v1',HERE.parent/'v001/build_bridge.py')
v1=importlib.util.module_from_spec(spec);spec.loader.exec_module(v1)
v1.HERE=HERE;v1.site=site
w=v1.w;G=w.Geometry
FLAGS=[(1.64,-5.12),(-1.64,5.12)]
ORIGINAL_MESH=v1.mesh
ORIGINAL_PALETTE=v1.palette_texture
ORIGINAL_RENDER=v1.render
ORIGINAL_TEXTURE=v1.texture_material

def rounded_profile(poly,cut=.1):
    """Clip each 2D corner; retain straight dressed-stone faces."""
    out=[]
    for i,p in enumerate(poly):
        a=Vector(poly[i-1]);b=Vector(p);c=Vector(poly[(i+1)%len(poly)])
        out.extend([tuple(b+(a-b)*cut),tuple(b+(c-b)*cut)])
    return out

def panel(g,poly,x,sign,seed,lod):
    if len(poly)<3:return
    cy=sum(p[1] for p in poly)/len(poly);cz=sum(p[0] for p in poly)/len(poly)
    if lod==2:
        g.face([(x,y,z) for z,y in poly],seed);return
    rng=random.Random(seed+round(cy*710)+round(cz*373))
    p=rounded_profile(poly,.08 if lod==0 else .05)
    # Worn profile and shallow bulge, with no perfectly stamped rectangular face.
    front=[]
    for z,y in p:
        front.append((z+(cz-z)*.05+rng.uniform(-.006,.006),y+(cy-y)*.09+rng.uniform(-.004,.004)))
    depth=.025+rng.uniform(-.006,.010)
    for i in range(len(p)):
        j=(i+1)%len(p)
        g.face([(x-sign*.019,p[i][1],p[i][0]),(x-sign*.019,p[j][1],p[j][0]),
                (x+sign*depth,front[j][1],front[j][0]),(x+sign*depth,front[i][1],front[i][0])],seed)
    g.face([(x+sign*depth,y,z) for z,y in front],seed)

def slab(g,x0,x1,z0,z1,h,seed,lod):
    if lod==2:
        g.face([(x0,h(z0),z0),(x1,h(z0),z0),(x1,h(z1),z1),(x0,h(z1),z1)],seed);return
    rng=random.Random(seed+round(z0*713)+round(x0*181))
    poly=rounded_profile([(x0,z0),(x1,z0),(x1,z1),(x0,z1)],.07)
    cx=(x0+x1)/2;cz=(z0+z1)/2
    inside=[(x+(cx-x)*.06+rng.uniform(-.006,.006),z+(cz-z)*.04+rng.uniform(-.005,.005)) for x,z in poly]
    for i in range(len(poly)):
        j=(i+1)%len(poly)
        g.face([(poly[i][0],h(poly[i][1])-.034,poly[i][1]),(poly[j][0],h(poly[j][1])-.034,poly[j][1]),
                (inside[j][0],h(inside[j][1]),inside[j][1]),(inside[i][0],h(inside[i][1]),inside[i][1])],seed)
    g.face([(x,h(z),z) for x,z in inside],seed)

def stone(lod):
    g=G();n=[19,15,11][lod]
    # Chunky individually cut arch stones, supported by a continuous dark core.
    for i in range(n):
        t0=math.pi*i/n+.0025;t1=math.pi*(i+1)/n-.0025
        poly=[(3.25*math.cos(t0),-1.55+2.05*math.sin(t0)),
              (3.25*math.cos(t1),-1.55+2.05*math.sin(t1)),
              (3.67*math.cos(t1),-1.55+2.44*math.sin(t1)),
              (3.67*math.cos(t0),-1.55+2.44*math.sin(t0))]
        # Near-side and far-side blocks frame a low-cost vault barrel.
        spans=[(-1.805,-1.35),(-1.35,0),(0,1.35),(1.35,1.805)] if lod==0 else [(-1.8,0),(0,1.8)]
        for j,(a,b) in enumerate(spans):
            v1.prism(g,poly,a+.004,b-.004,(i*5+j*3)%6,.042 if lod==0 and j in [0,3] else (.016 if lod<2 else 0))
    for side in [-1,1]:
        # Fewer, larger courses read as hand-set bridge masonry at gameplay distance.
        # The slight course-height drift keeps the silhouette calm while avoiding a
        # machine-made brick grid.
        for row in range(8):
            ya=-1.73+row*.36+.008;yb=ya+.344
            cuts=[-5.4];z=-5.4+(.36 if row%2 else .69)
            while z<5.20:cuts.append(z);z+=.68+.11*math.sin(row*4+z*5)
            cuts.append(5.4)
            for col,(a,b) in enumerate(zip(cuts,cuts[1:])):
                for half in [-1,1]:
                    if half==-1 and a>=0 or half==1 and b<=0:continue
                    poly=[(a+.005,ya),(b-.005,ya),(b-.005,yb),(a+.005,yb)]
                    poly=v1.clip(poly,lambda z,y:half*z)
                    radius=lambda y:3.67*math.sqrt(max(0,1-((y+1.55)/2.44)**2)) if y>=-1.55 else 3.67
                    r0=radius(ya);r1=radius(yb)
                    poly=v1.clip(poly,lambda z,y:half*z-(r0+(r1-r0)*(y-ya)/(yb-ya))-.003)
                    if not poly:continue
                    poly=v1.clip(poly,lambda z,y:site.deck_height(z)-.095-y)
                    panel(g,poly,side*1.772,side,row*19+col*3,lod)
    # Broad paving slabs echo the concept and keep the crown legible.
    nz=[18,13,9][lod];nx=[4,3,2][lod]
    for j in range(nz):
        a=-5.4+10.8*j/nz;b=-5.4+10.8*(j+1)/nz
        cuts=[-1.43]+[-1.43+2.86*(i+(.33 if j%2 else -.15))/nx for i in range(1,nx)]+[1.43]
        for i,(xa,xb) in enumerate(zip(cuts,cuts[1:])):
            slab(g,xa+.006,xb-.006,a+.005,b-.005,site.deck_height,3+j*5+i*2,lod)
    for side in [-1,1]:
        n=[18,13,9][lod]
        for i in range(n):
            a=-5.4+10.8*i/n;b=-5.4+10.8*(i+1)/n
            temp=G()
            w.rock(temp,(side*1.64-.18,-.085,a+.004),(side*1.64+.18,.20,b-.004),i*53+17,1 if lod==0 else 2,.042)
            v1.shifted(temp,lambda p:Vector((p.x,p.y+site.deck_height(p.z),p.z)));v1.append(g,temp)
        for zi,z in enumerate([-5.12,-2.56,0,2.56,5.12]):
            base=site.deck_height(z)
            for row in range(3 if lod<2 else 1):
                nr=3 if lod<2 else 1
                w.rock(g,(side*1.64-.20,base+.20+row*.65/nr,z-.20),
                    (side*1.64+.20,base+.20+(row+1)*.65/nr-.006,z+.20),101+zi*13+row*5,1 if lod<2 else 2,.04)
            w.rock(g,(side*1.64-.25,base+.84,z-.25),(side*1.64+.25,base+.97,z+.25),50+zi*7,1 if lod==0 else 2,.027)
    return g

def wood(lod):
    g=G()
    for side in [-1,1]:
        for a,b in zip([-5.12,-2.56,0,2.56],[-2.56,0,2.56,5.12]):
            for h in [.45,.77]:
                ya=site.deck_height(a)+h;yb=site.deck_height(b)+h
                tmp=G();w.bevel_box(tmp,(side*1.64-.080,ya-.068,a-.06),(side*1.64+.080,ya+.068,b+.06),0,0 if lod==0 else 2,.026)
                v1.shifted(tmp,lambda p:Vector((p.x,p.y+(yb-ya)*(p.z-a)/(b-a)+.017*math.sin(math.pi*(p.z-a)/(b-a)),p.z)))
                v1.append(g,tmp)
    for x,z in FLAGS:
        base=site.deck_height(z)+.97
        w.bevel_box(g,(x-.071,base,z-.071),(x+.071,base+1.69,z+.071),0,0 if lod<2 else 2,.014)
        w.bevel_box(g,(x-.08,base+1.50,z-.49),(x+.08,base+1.62,z+.49),0,0 if lod<2 else 2,.018)
        # One forged foot socket; the flagpole is seated on the stone cap.
        w.bevel_box(g,(x-.088,base,z-.088),(x+.088,base+.13,z+.088),2,0 if lod==0 else 2,.01)
    return g

def banner_point(x,z,u,t,off=0):
    base=site.deck_height(z)+.97+1.49
    # Draped fabric hangs clear of the cap and carries a small swallowtail.
    return (x+.11+off+.065*math.sin(u*math.pi*2.5+t*2)*t,
            base-t*(1.13+.14*abs(2*u-1)),z+(u-.5)*.72)

def banners(lod):
    cloth=G();trim=G()
    for x,z in FLAGS:
        nx,ny=[(8,12),(5,7),(3,4)][lod]
        pos=lambda u,t,off=0:banner_point(x,z,u,t,off)
        for j in range(ny):
            for i in range(nx):
                u=i/nx;t=j/ny;du=1/nx;dt=1/ny
                coords=[(u,t),(u+du,t),(u+du,t+dt),(u,t+dt)]
                cloth.face([pos(*p) for p in coords],0,[(a,1-b) for a,b in coords])
                cloth.face([pos(a,b,-.006) for a,b in reversed(coords)],0,[(1-a,1-b) for a,b in reversed(coords)])
        for s in [-1,1]:
            offset=.009 if s==1 else -.015
            # Simple lily silhouette cut from cloth, substantially larger than tiny filigree.
            shape=[(.47,.60),(.43,.53),(.44,.47),(.35,.48),(.29,.44),(.28,.38),(.32,.35),(.37,.36),(.45,.44),(.45,.34),(.40,.29),(.50,.19),(.60,.29),(.55,.34),(.55,.44),(.63,.36),(.68,.35),(.72,.38),(.71,.44),(.65,.48),(.56,.47),(.57,.53),(.53,.60)]
            center=(.50,.43)
            for a,b in zip(shape,shape[1:]+shape[:1]):trim.face([pos(*center,offset),pos(*a,offset),pos(*b,offset)],10)
            for a,b in [(0,.027),(.973,1)]:
                for j in range(ny):trim.face([pos(a,j/ny,offset),pos(b,j/ny,offset),pos(b,(j+1)/ny,offset),pos(a,(j+1)/ny,offset)],4)
        base=site.deck_height(z)+.97
        pts=[(x-.11,base+1.70,z-.11),(x+.11,base+1.70,z-.11),(x+.11,base+1.70,z+.11),(x-.11,base+1.70,z+.11)]
        for i in range(4):trim.face([pts[i],pts[(i+1)%4],(x,base+1.94,z)],4)
        # Two small ties between pole and fabric, not rows of metal rivets.
        for dz in [-.27,.27]:w.bevel_box(trim,(x+.065,base+1.43,z+dz-.018),(x+.13,base+1.60,z+dz+.018),4,2)
    return cloth,trim

ROCK_LAYOUT=[]
def rocks(lod):
    g=G();rng=random.Random(70261)
    positions=[]
    # Large stones are composed in asymmetrical groups beside the abutments.
    for x,z,r in [(-2.38,-3.63,.65),(-2.93,-3.92,.39),(-2.03,3.69,.58),(2.20,-3.50,.54),(2.82,-3.80,.34),(2.45,3.68,.71),(3.23,3.45,.33),(-3.0,3.24,.30)]:
        positions.append((x,z,r,rng.uniform(.75,1.3)))
    for i in range(110):
        x=rng.uniform(-5.0,5.0);side=rng.choice([-1,1]);z=side*rng.uniform(2.85,4.18)
        if abs(x)<1.9 and abs(z)>3.6:continue
        positions.append((x,z,rng.uniform(.075,.27),rng.uniform(.7,1.4)))
    for i in range(27):
        x=rng.choice([-1,1])*rng.uniform(1.45,2.75);z=rng.choice([-1,1])*rng.uniform(5.45,6.75)
        positions.append((x,z,rng.uniform(.035,.11),rng.uniform(.8,1.3)))
    ROCK_LAYOUT[:]=positions
    for i,(x,z,r,stretch) in enumerate(positions):
        if lod==2 and r<.4 or lod==1 and r<.095:continue
        bm=bmesh.new();bmesh.ops.create_icosphere(bm,subdivisions=2 if lod==0 and r>.48 else 1,radius=1)
        y=site.terrain_height(x,z)+r*.26
        for vert in bm.verts:
            p=vert.co.copy()
            # Flatten the crown, shear the mass and keep planar facets. This gives
            # shoreline stones a quarried silhouette instead of smooth spheres.
            f=1+.18*math.sin(p.x*3.1+i*1.7)+.10*math.cos(p.z*4.3-i)
            px=p.x*r*stretch*f+p.z*r*.13*math.sin(i*.91)
            pz=p.z*r*(.78+.10*math.sin(i))*f
            py=p.y*r*.56*f
            if py>r*.18:py=r*.18+(py-r*.18)*.42
            vert.co=Vector((x+px,y+py,z+pz))
        for f in bm.faces:g.face([tuple(p.co) for p in f.verts],i*7%6)
        bm.free()
    return g

def vegetation(lod):
    g=G();rng=random.Random(58322)
    centers=[]
    for x,z in [(-2.1,-4.18),(-3.05,-3.97),(2.1,-4.1),(3.0,-3.78),(-2.1,4.12),(-3.4,3.66),(2.05,4.40),(3.2,3.96)]:
        for j in range(11):centers.append((x+rng.uniform(-.55,.55),z+rng.uniform(-.50,.50),j%3))
    for j in range(78):
        x=rng.uniform(-5.1,5.1);z=rng.choice([-1,1])*rng.uniform(3.65,6.2)
        if abs(x)>1.97:centers.append((x,z,1))
    for i,(x,z,kind) in enumerate(centers):
        # All random choices are consumed before LOD filtering.
        blades=[(rng.uniform(0,math.tau),rng.uniform(.22,.52)*(1.45 if kind==0 else 1),rng.uniform(.030,.065),rng.uniform(.14,.38),rng.randrange(3)) for _ in range(7)]
        if lod==2 or lod==1 and i%2:continue
        y=site.terrain_height(x,z)+.005
        for angle,h,width,bend,color_slot in blades[:7 if lod==0 else 4]:
            dx=math.cos(angle);dz=math.sin(angle)
            pts=[]
            for t,ww in [(0,.65),(.5,1),(1,.015)]:
                cx=x+dx*bend*t*t;cz=z+dz*bend*t*t
                pts.extend([(cx-dz*width*ww,y+h*t,cz+dx*width*ww),(cx+dz*width*ww,y+h*t,cz-dx*width*ww)])
            for k in range(2):
                q=[pts[k*2],pts[k*2+1],pts[k*2+3],pts[k*2+2]]
                u0=color_slot/3+.025;u1=(color_slot+1)/3-.025
                uv=[(u0,k*.5),(u1,k*.5),(u1,(k+1)*.5),(u0,(k+1)*.5)]
                g.face(q,0,uv);g.face(list(reversed([(a,b,c+.0007) for a,b,c in q])),0,list(reversed(uv)))
    return g

def botany(lod):
    g=G();rng=random.Random(82891)
    for i in range(42):
        x=rng.choice([-1,1])*rng.uniform(2.0,4.25);z=rng.choice([-1,1])*rng.uniform(3.9,5.55)
        phase=rng.uniform(0,6.28);size=rng.uniform(.16,.25)
        if lod==2 or lod==1 and i%2:continue
        y=site.terrain_height(x,z)+.025
        for j in range(6):
            a=phase+j*math.tau/6;dx=math.cos(a);dz=math.sin(a);r=size*(.83+.15*math.sin(i+j))
            # Broad bent leaves give a different silhouette from grass spikes.
            root=(x,y,z);mid=(x+dx*r*.52,y+r*.48,z+dz*r*.52);tip=(x+dx*r,y+r*.28,z+dz*r)
            left=(mid[0]-dz*r*.22,mid[1],mid[2]+dx*r*.22);right=(mid[0]+dz*r*.22,mid[1],mid[2]-dx*r*.22)
            for face in [[root,left,tip],[root,tip,right]]:
                g.face(face,8+j%2);g.face(list(reversed([(a,b-.001,c) for a,b,c in face])),8+j%2)
        if i%3==0:
            stem_top=y+.34
            for j in range(5):
                a=j*math.tau/5;dx=math.cos(a);dz=math.sin(a)
                g.face([(x,stem_top,z),(x+dx*.065-dz*.024,stem_top+.012,z+dz*.065+dx*.024),
                        (x+dx*.095,stem_top+.022,z+dz*.095),(x+dx*.065+dz*.024,stem_top+.012,z+dz*.065-dx*.024)],10)
    # Rounded low shrubs anchor the bridge to the banks. Leaf diamonds share the
    # palette atlas and stay under a thousand triangles for the full dressing.
    shrub_sites=[(-2.55,-3.72),(-3.18,-3.48),(-2.25,3.78),(-3.25,3.58),
                 (2.45,-3.66),(3.18,-3.43),(2.34,3.82),(3.30,3.55),
                 (-2.30,-4.55),(2.23,4.58),(-3.78,-4.08),(3.75,4.05)]
    for si,(x,z) in enumerate(shrub_sites):
        if lod==2 or lod==1 and si%2:continue
        y=site.terrain_height(x,z)+.025
        count=9 if lod==0 else 5
        for j in range(count):
            a=(j*.618+si*.173)*math.tau;r=.08+.24*((j*37+si*11)%10)/10
            cx=x+math.cos(a)*r;cz=z+math.sin(a)*r
            h=.13+.18*((j*19+si*7)%9)/9;s=.10+.055*((j+si)%4)
            # Tilted, broad four-point leaves; paired faces remain visible from
            # the game's high camera without instanced per-blade objects.
            dx=math.cos(a);dz=math.sin(a);px=-dz;pz=dx
            leaf=[(cx-dx*s*.72,y+h-.015,cz-dz*s*.72),
                  (cx+px*s*.42,y+h+.018,cz+pz*s*.42),
                  (cx+dx*s,y+h+.035,cz+dz*s),
                  (cx-px*s*.42,y+h-.006,cz-pz*s*.42)]
            g.face(leaf,8+(j+si)%2);g.face(list(reversed([(a,b-.002,c) for a,b,c in leaf])),8+(j+si)%2)
    # Small moss islands soften selected wall joints, never cover the whole stone.
    for side in [-1,1]:
        for i in range(32 if lod==0 else 12):
            z=rng.uniform(-5.15,5.15);y=site.deck_height(z)+rng.uniform(.02,.16)
            r=rng.uniform(.025,.060);x=side*1.824
            pts=[(x,y+math.sin(a)*r*.7,z+math.cos(a)*r*1.7) for a in [j*math.tau/7 for j in range(7)]]
            g.face(pts,5+i%2)
    return g

def water():
    g=G();rng=random.Random(883)
    for i in range(56):
        a=-7+i*.25;b=a+.25;wa=site.channel_half_width(a)+.37;wb=site.channel_half_width(b)+.37
        for j in range(9):
            t0=-1+2*j/9;t1=-1+2*(j+1)/9
            # Continuous UVs and one material remove the old checkerboard pattern.
            pts=[(a,site.WATER_Y,wa*t0),(b,site.WATER_Y,wb*t0),(b,site.WATER_Y,wb*t1),(a,site.WATER_Y,wa*t1)]
            uv=[((x+7)/14,(z+3.4)/6.8) for x,y,z in pts]
            g.face(pts,11,uv)
    return g

def ripples():
    g=G();rng=random.Random(713)
    # Long broken streaks suggest flow, concentrated near shoreline rocks.
    for i in range(150):
        x=rng.uniform(-6.7,6.7);z=rng.uniform(-2.88,2.88);length=rng.uniform(.10,.40);width=rng.uniform(.006,.022)
        y=site.WATER_Y+.006
        g.face([(x-length,y,z),(x+length,y,z+.016),(x+length*.8,y,z+width+.016),(x-length*.7,y,z+width)],13 if i%4==0 else 12)
    return g

def palette():
    ORIGINAL_PALETTE()
    # This is a newly authored lookup palette, not a retouch of the generated limestone.
    colors=[(.46,.255,.090),(.32,.165,.052),(.12,.14,.135),(.04,.17,.52),
            (.68,.43,.12),(.34,.43,.055),(.49,.53,.095),(.69,.57,.32),
            (.22,.38,.070),(.33,.48,.085),(.95,.88,.61),(.075,.31,.34),
            (.10,.37,.40),(.49,.71,.67),(.40,.365,.27),(.64,.59,.44)]
    im=bpy.data.images['T_Bridge_Palette'];pixels=[]
    for y in range(256):
        for x in range(256):
            p=(y//64)*4+x//64;c=colors[p]
            t=.035*math.sin(y*.32+.9*math.sin(x*.07))+.015*math.sin(y*.95) if p<2 else 0
            pixels.extend([v+t for v in c]+[1])
    im.pixels.foreach_set(pixels);im.save()

    # One-material limestone atlas. Each tile reuses the authored ImageGen
    # limestone grain with a restrained warm/cool tint, so the value variation is
    # texture-based and survives a simple Unity lit shader.
    src=bpy.data.images.load(str(HERE/'Textures/T_Bridge_Limestone_BaseColor.png'),check_existing=True)
    sw,sh=src.size;src_pixels=array('f',[0])*(sw*sh*4);src.pixels.foreach_get(src_pixels)
    size=1024;tile=size//4;stone_pixels=array('f',[0])*(size*size*4)
    tints=[(.90,.86,.78),(.97,.91,.82),(.83,.85,.83),(.98,.91,.79),
           (.92,.88,.81),(.86,.86,.83),(.96,.87,.75),(.91,.92,.89),
           (.81,.83,.81),(.95,.88,.80),(.88,.85,.78),(.99,.94,.86),
           (.85,.83,.80),(.93,.91,.86),(.88,.88,.85),(.96,.91,.82)]
    for y in range(size):
        row=min(3,y//tile);ly=(y%tile)/(tile-1);sy=min(sh-1,int(ly*(sh-1)))
        for x in range(size):
            col=min(3,x//tile);lx=(x%tile)/(tile-1);sx=min(sw-1,int(lx*(sw-1)))
            tint=tints[row*4+col];si=(sy*sw+sx)*4;di=(y*size+x)*4
            broad=.94+.06*math.sin(lx*9.1+ly*6.7+row*1.3-col*.9)
            for k in range(3):stone_pixels[di+k]=max(0,min(1,src_pixels[si+k]*tint[k]*broad))
            stone_pixels[di+3]=1
    im=bpy.data.images.new('T_Bridge_StoneAtlas',width=size,height=size,alpha=False)
    im.pixels.foreach_set(stone_pixels);im.filepath_raw=str(HERE/'Textures/T_Bridge_StoneAtlas_BaseColor.png');im.file_format='PNG';im.save()
    im=bpy.data.images['T_Bridge_Grass'];im.scale(96,128);pixels=[]
    for y in range(128):
        t=y/127
        for x in range(96):
            slot=min(2,x//32)
            roots=[(.12,.245,.018),(.17,.31,.022),(.24,.34,.035)][slot]
            tips=[(.48,.62,.085),(.62,.67,.12),(.72,.64,.15)][slot]
            grain=.018*math.sin(x*.71+y*.19+slot)
            pixels.extend([roots[k]*(1-t)+tips[k]*t+grain for k in range(3)]+[1])
    im.pixels.foreach_set(pixels);im.save()

    # A coherent painterly water surface. Lighting stays dynamic; the texture
    # contributes broad turquoise depth bands and sparse warm reflected flecks.
    size=512;pixels=[]
    for y in range(size):
        v=y/(size-1)
        for x in range(size):
            u=x/(size-1)
            band=.5+.28*math.sin(u*22+math.sin(v*9)*1.4)+.17*math.sin(u*61+v*17)
            edge=abs(v-.5)*2
            deep=(.035,.20,.25);shallow=(.10,.42,.47);bank=(.24,.55,.54)
            mix=max(0,min(1,.26+.60*band))
            c=[deep[k]*(1-mix)+shallow[k]*mix for k in range(3)]
            haze=max(0,min(1,(edge-.67)/.33))*.36
            c=[c[k]*(1-haze)+bank[k]*haze for k in range(3)]
            pixels.extend(c+[1])
    im=bpy.data.images.new('T_Bridge_Water',width=size,height=size,alpha=False)
    im.pixels.foreach_set(pixels);im.filepath_raw=str(HERE/'Textures/T_Bridge_Water_BaseColor.png');im.file_format='PNG';im.save()

def texture(name,file,rough=.88):
    if name=='M_Bridge_Stone':file='T_Bridge_StoneAtlas_BaseColor.png'
    mat=ORIGINAL_TEXTURE(name,file,rough)
    if name=='M_Bridge_Grass':
        # Mild diffuse transmission for foliage; final Unity uses shared grass lighting.
        bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Subsurface Weight'].default_value=.08
    return mat

def mesh(g,name,coll,mat,palette=False):
    if name=='SM_Bridge_Water':
        water_mat=bpy.data.materials.get('M_Bridge_Water')
        if not water_mat:
            water_mat=ORIGINAL_TEXTURE('M_Bridge_Water','T_Bridge_Water_BaseColor.png',.28)
            bs=water_mat.node_tree.nodes.get('Principled BSDF')
            bs.inputs['Metallic'].default_value=.04
        mat=water_mat;palette=False
    stone_surface=('Stone' in name or 'Rocks' in name) and 'COL_' not in name
    if stone_surface:
        # Assign atlas UVs before mesh triangulation. Faces created from the same
        # stone share their patch id and therefore keep one consistent tint.
        for fi,(face,patch) in enumerate(zip(g.f,g.patches)):
            pts=[Vector(g.v[i]) for i in face]
            if len(pts)<3:continue
            n=(pts[1]-pts[0]).cross(pts[2]-pts[0]).normalized();t=(pts[1]-pts[0]).normalized();bt=n.cross(t)
            coords=[(p.dot(t),p.dot(bt)) for p in pts]
            ua,ub=min(p[0] for p in coords),max(p[0] for p in coords);va,vb=min(p[1] for p in coords),max(p[1] for p in coords)
            tile=patch%16;col=tile%4;row=tile//4;margin=.025
            g.uvs[fi]=[((col+margin+(u-ua)/max(1e-6,ub-ua)*(1-2*margin))/4,
                        (row+margin+(v-va)/max(1e-6,vb-va)*(1-2*margin))/4) for u,v in coords]
    ob=ORIGINAL_MESH(g,name,coll,mat,palette)
    # Faceted rock and dressed-stone planes carry the hand-built style. Rounded
    # edges are real geometry, so smoothing no longer melts boulders into spheres.
    if stone_surface:
        for p in ob.data.polygons:p.use_smooth=False
    if 'Grass_LOD' in name:
        lod=int(name[-1]);plants=botany(lod)
        if plants.f:
            extra=ORIGINAL_MESH(plants,f'SM_Bridge_Botany_LOD{lod}',coll,bpy.data.materials['M_Bridge_Palette'],True)
            # Small leafy plants have their own wind mask; rigid moss remains zero.
            colors=extra.data.color_attributes.new(name='WindMask',type='FLOAT_COLOR',domain='POINT')
            for v,color in zip(extra.data.vertices,colors.data):
                p=w.U(v.co);color.color=(max(0,min(1,(p[1]-site.terrain_height(p[0],p[2]))/.38)) if abs(p[0])>1.9 else 0,0,0,1)
            v1.REPORT['meshes'][extra.name]=w.audit(extra)
    return ob

ORIGINAL_EXPORT=v1.export
def export(name,objects):
    if name.startswith('SM_Bridge_Dressing'):
        lod=int(name[-1]);extra=bpy.data.objects.get(f'SM_Bridge_Botany_LOD{lod}')
        if extra:objects=objects+[extra]
    ORIGINAL_EXPORT(name,objects)

def render(name,pos,target,scale,res=(1600,1100)):
    sc=bpy.context.scene
    sc.cycles.samples=48
    sc.world.node_tree.nodes['Background'].inputs[1].default_value=.48
    sc.view_settings.exposure=.05
    sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.78,.84,.91,1)
    sun=bpy.data.objects.get('Sun');sun.data.energy=2.8;sun.data.color=(1,.87,.68);sun.data.angle=math.radians(13)
    # A neutral warm ground and generous framing; all actual meshes remain visible.
    if bpy.data.materials.get('Studio_Sand'):
        bs=bpy.data.materials['Studio_Sand'].node_tree.nodes.get('Principled BSDF')
        bs.inputs['Base Color'].default_value=(.85,.76,.62,1)
    if name in ['Bridge_Hero.png','Bridge_Realtime_Eevee.png']:
        pos=(15,8.2,-11);target=(0,.05,0);scale=14.8
    ORIGINAL_RENDER(name,pos,target,scale,res)

v1.bridge_stone=stone;v1.wood=wood;v1.banners=banners;v1.rocks=rocks
v1.grass=vegetation;v1.water=water;v1.ripples=ripples
v1.palette_texture=palette;v1.texture_material=texture;v1.mesh=mesh;v1.export=export;v1.render=render

if __name__=='__main__':
    v1.main()
    # Store a clean opening view reflecting the final lighting, without changing v001.
    bpy.context.scene.render.engine='CYCLES'
    v1.camera((16,9,-10),(0,.05,0),18.3)
    bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'Bridge_Stone_A.blend'))
