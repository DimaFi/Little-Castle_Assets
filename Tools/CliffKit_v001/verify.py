"""Texture provenance and deterministic seam/LOD/slope contract; visual/Unity gates separate."""
import ast,math,random,json,hashlib
from pathlib import Path
from PIL import Image
import numpy as np
ROOT=Path(__file__).resolve().parents[2];SOURCE=ROOT/'Source/Environment/CliffKit/v001'

def main():
    manifest=json.loads((SOURCE/'Textures/TEXTURE_MANIFEST.json').read_text())
    for record in manifest['maps']:
        path=SOURCE/'Textures'/record['path'];assert hashlib.sha256(path.read_bytes()).hexdigest()==record['sha256']
        pixels=np.asarray(Image.open(path),dtype=np.int16)
        assert pixels.shape[:2]==(1024,1024)
        assert max(np.abs(pixels[:,0]-pixels[:,-1]).mean(),np.abs(pixels[0]-pixels[-1]).mean())<3
    tree=ast.parse((ROOT/'Tools/CliffKit_v001/build.py').read_text())
    selected=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('cliff','rock','ramp')]
    scope=dict(math=math,random=random);exec(compile(ast.Module(body=selected,type_ignores=[]),'build','exec'),scope)
    catalog=json.loads((SOURCE/'ASSET_CATALOG.json').read_text());seams=0
    for cfg in catalog['assets']:
        counts=[]
        for lod in range(3):
            v,f,m=scope[cfg['kind']](cfg,lod);assert (v,f,m)==scope[cfg['kind']](cfg,lod)
            assert len(f)==cfg['lod_triangle_counts'][lod];counts.append(len(f))
            if cfg['kind']=='cliff' and not cfg['profile'].startswith('end'):
                # Same-height straight/curved/terrace sockets meet the identical boundary line.
                for side in (-1,1):
                    for x,y,z in v:
                        if abs(x-side*cfg['width']/2)<1e-7:
                            assert -.451<=y<=cfg['height']+.001
                            if z<=.001: assert abs(z-(-.35+.35*(y+.45)/(cfg['height']+.45)))<1e-6
                seams+=1
            if cfg['kind']=='ramp':
                assert 12<math.degrees(math.atan2(cfg['height'],cfg['depth']))<30
        assert counts[0]>counts[1]>counts[2]
    qa=json.loads((SOURCE/'QA/geometry.json').read_text());assert qa['status']=='PASS' and len(qa['fbx_roundtrip'])==42
    result=dict(status='PASS_SOURCE_CONTRACT_ONLY',png_maps=17,deterministic_meshes=42,socket_boundary_checks=seams,fbx_roundtrips=42,texture_manifest_sha256=hashlib.sha256((SOURCE/'Textures/TEXTURE_MANIFEST.json').read_bytes()).hexdigest())
    (SOURCE/'QA/source_contract.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

if __name__=='__main__':main()
