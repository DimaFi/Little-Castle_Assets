#!/usr/bin/env python3
"""Create deterministic tileable concept PBR texture maps; Pillow + numpy only.
These maps are PROTOTYPE source materials, not scan-quality PBR/baked AO.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image

MATERIALS = ('Rock_Limestone_A','Rock_Limestone_B','GrassCap_A')

def clamp(x):
    return np.clip(x,0,1)

def noise(rng, n, pixels):
    """Periodic smooth value noise: sampled pixel centers with wrapped lattice."""
    a=rng.random((n,n),dtype=np.float32)
    axis=(np.arange(pixels,dtype=np.float32)+0.5)*(n/pixels)
    idx=np.floor(axis).astype(np.int32)%n
    f=axis-np.floor(axis)
    f=f*f*(3-2*f)
    fx=f[None,:]
    fy=f[:,None]
    i=(idx+1)%n
    v00=a[idx[:,None],idx[None,:]]
    v10=a[idx[:,None],i[None,:]]
    v01=a[i[:,None],idx[None,:]]
    v11=a[i[:,None],i[None,:]]
    return ((v00*(1-fx)+v10*fx)*(1-fy)
          +(v01*(1-fx)+v11*fx)*fy)

def fractal(seed,pixels,freq=(4,8,16,32,64,128),weights=(.40,.25,.16,.10,.06,.03)):
    rng=np.random.default_rng(seed)
    z=np.zeros((pixels,pixels),dtype=np.float32)
    for n,w in zip(freq,weights): z+=w*noise(rng,n,pixels)
    return z

def save_l(path,a,mode='L'):
    Image.fromarray((clamp(a)*255+.5).astype('uint8'),mode).save(path,optimize=True)

def save_rgb(path,a):
    Image.fromarray((clamp(a)*255+.5).astype('uint8'),'RGB').save(path,optimize=True)

def save_height_normal(path,height,scale=3):
    # Tangent space DirectX/OpenGL convention is explicitly OPENGL (+Y).
    dx=(np.roll(height,-1,1)-np.roll(height,1,1))*.5
    dy=(np.roll(height,-1,0)-np.roll(height,1,0))*.5
    nx=-dx*scale;ny=-dy*scale;nz=np.ones_like(nx)
    norm=np.sqrt(nx*nx+ny*ny+nz*nz)
    save_rgb(path,np.stack(((nx/norm+.999999)*.5,(ny/norm+.999999)*.5,nz/norm),axis=-1))

def maps(pixels,seed,material,out):
    out.mkdir(parents=True,exist_ok=True)
    n0=fractal(seed,pixels);n1=fractal(seed+3,pixels);n2=fractal(seed+9,pixels)
    y,x=np.mgrid[0:pixels,0:pixels]
    if material.startswith('Rock'):
        # Sinusoidal layers with a periodic displacement field. Geometry does the silhouettes.
        warp=(n1-.5)*16.0
        strata=.5+.5*np.sin(2*np.pi*(y/pixels*9 +warp/pixels*9))
        fine=noise(np.random.default_rng(seed+37),128,pixels)
        crevice=(1-n2)**2
        height=clamp(.12+.68*n0+.14*strata+.12*(fine-.5)-.13*crevice)
        earthy=material.endswith('B')
        dark=np.array([.35,.295,.245] if earthy else [.47,.435,.36],dtype=np.float32)
        light=np.array([.69,.605,.48] if earthy else [.78,.733,.61],dtype=np.float32)
        shade=clamp(.16+.62*n0+.12*strata-.13*crevice)
        rgb=dark[None,None,:]+shade[:,:,None]*(light-dark)[None,None,:]
        rgb*= (.92+.12*n1)[:,:,None]
        moss=clamp(((.58-n2)*2.2)*(.25+.7*(1-strata)) + .12*(.5-n0))
        # Moss mask is intended for limited patches in Blender; Unity must review blending.
        rough=clamp(.75+.12*(n1-.5)+.07*strata)
        ao=clamp(1-.30*crevice-.09*(1-n0)) # visual cavity approximation, not baked mesh AO.
        save_l(out/'Height.png',height)
        save_height_normal(out/'Normal_OpenGL.png',height,scale=9)
        save_l(out/'MossMask.png',moss)
        save_l(out/'Roughness.png',rough)
        save_l(out/'AO_Approx.png',ao)
        save_rgb(out/'BaseColor.png',rgb)
    else:
        # Grass cap is color-based ground coverage, NOT replacement for geometry grass.
        p=clamp(.22+.65*n0+.10*(n1-.5))
        a=np.array([.17,.27,.105],dtype=np.float32)
        b=np.array([.49,.56,.25],dtype=np.float32)
        rgb=a[None,None,:]+p[:,:,None]*(b-a)[None,None,:]
        height=clamp(.42+.28*n0+.11*(n2-.5))
        save_rgb(out/'BaseColor.png',rgb)
        save_l(out/'Height.png',height)
        save_height_normal(out/'Normal_OpenGL.png',height,scale=2.5)
        save_l(out/'Roughness.png',clamp(.86+.08*(n1-.5)))
        save_l(out/'AO_Approx.png',clamp(.92+.08*n0))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--out',type=Path,default=Path(__file__).parent/'Textures')
    ap.add_argument('--size',type=int,default=1024)
    ap.add_argument('--seed',type=int,default=20261009)
    args=ap.parse_args()
    if not 128<=args.size<=2048 or args.size&(args.size-1):ap.error('--size must be power of two in [128,2048]')
    files=[]
    for i,name in enumerate(MATERIALS):
        dest=args.out/name
        maps(args.size,args.seed+i*137,name,dest)
        for p in sorted(dest.glob('*.png')):
            files.append({'path':p.relative_to(args.out).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size})
    (args.out/'TEXTURE_MANIFEST.json').write_text(json.dumps({'version':1,'seed':args.seed,'size':args.size,'maps':files,'remarks':'Seamless procedural prototype; AO_Approx is not baked AO; Normal_OpenGL uses +Y'},indent=2)+'\n',encoding='utf-8')
    print(f'Generated {len(files)} texture maps in {args.out}')

if __name__=='__main__':main()
