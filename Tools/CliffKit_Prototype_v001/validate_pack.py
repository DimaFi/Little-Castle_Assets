#!/usr/bin/env python3
"""Source-only validation without Blender. DOES NOT validate FBX, Unity or visuals."""
from __future__ import annotations
import ast
import hashlib
import json
import math
import random
from pathlib import Path
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parent


def check_textures():
    m=json.loads((ROOT/'Textures/TEXTURE_MANIFEST.json').read_text('utf-8'))
    assert m['size']>=128 and len(m['maps'])==17
    for record in m['maps']:
        p=ROOT/'Textures'/record['path']
        assert p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==record['sha256']
        im=np.asarray(Image.open(p),dtype=np.int16)
        assert im.shape[:2]==(m['size'],m['size'])
        # Same sample density on periodic boundary, allow at most a few 8-bit LSBs.
        assert max(np.abs(im[:,0]-im[:,-1]).mean(),np.abs(im[0]-im[-1]).mean())<3.0, p
        if p.name=='Normal_OpenGL.png':
            assert im.shape[2]==3 and (im[:,:,2]>127).all()
    return len(m['maps'])


def check_geometry():
    path=ROOT/'build_cliff_kit.py'
    tree=ast.parse(path.read_text(encoding='utf-8'))
    keep=['cliff_mesh','rock_mesh','ramp_mesh']
    functions=[x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name in keep]
    assert len(functions)==3
    # Extract PURE mesh equations, no import of bpy; a test double captures geometry.
    def capture(name,verts,faces,mats,materials,uv):return (verts,faces,mats)
    scope={'math':math,'geometry_object':capture}
    exec(compile(ast.Module(body=functions,type_ignores=[]),str(path),'exec'),scope)
    archetypes=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='ARCHETYPES' for t in n.targets))
    # Evaluate only the local constant archetype list; do not import bpy.
    config_space={'dict':dict}
    exec(compile(ast.Module(body=[archetypes],type_ignores=[]),str(path),'exec'),config_space)
    cfgs=config_space['ARCHETYPES']
    assert len(cfgs)>=12
    checks=0
    for cfg in cfgs:
        assert cfg['width']>0 and cfg['height']>0 and cfg['depth']>0
        counts=[]
        for lod in range(3):
            vs,fs,ms=scope[cfg['kind']+'_mesh'](cfg,lod,random.Random('stable:'+cfg['id']),[None,None])
            assert len(fs)==len(ms) and len(fs)>0 and all(len(f)==3 for f in fs)
            assert all(math.isfinite(a) for v in vs for a in v)
            assert all(0<=i<len(vs) for f in fs for i in f)
            counts.append(len(fs))
            if cfg['kind']=='ramp':
                target=math.degrees(math.atan2(cfg['height'],cfg['depth']))
                assert 12<target<25, (cfg['id'],target)
            if cfg['kind']=='cliff':
                # Cap faces are guaranteed up-facing from source winding.
                cap=[f for f,m in zip(fs,ms) if m==1]
                assert cap
                def cy(f):
                    a,b,c=(vs[f[0]],vs[f[1]],vs[f[2]])
                    return (b[2]-a[2])*(c[0]-a[0])-(b[0]-a[0])*(c[2]-a[2])
                assert all(cy(f)>0 for f in cap),cfg['id']
            checks+=1
        assert counts[0]>counts[1]>counts[2],(cfg['id'],counts)
    return len(cfgs),checks

if __name__=='__main__':
    n=check_textures();a,meshes=check_geometry()
    print('SOURCE_ONLY_PASS',n,'png_maps',a,'archetypes',meshes,'concept_mesh_checks')
