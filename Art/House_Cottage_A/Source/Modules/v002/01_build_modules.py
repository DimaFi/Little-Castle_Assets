"""First small batch: reusable stone, bowed timber, curved tile. No UV yet.
Run in a fresh background Blender process, never the user's open scene.
Requires --output <new directory>; existing .blend is never overwritten.
"""
from pathlib import Path
import sys, argparse, math
sys.path.insert(0,str(Path(__file__).parent))
from geometry import *

args=argparse.ArgumentParser(); args.add_argument('--output',required=True)
cfg=args.parse_args(sys.argv[sys.argv.index('--')+1:])
out=Path(cfg.output).resolve(); out.mkdir(parents=True,exist_ok=True)
blend=out/'Cottage_A_Primitives.blend'
if blend.exists(): raise FileExistsError('Choose a new output directory to preserve manual edits: '+str(blend))
s,mat=setup(); col=collection('MODULE_LIBRARY')
stone=box('SM_Foundation_Block_A',(.0,0,.135),(.52,.34,.27),col,mat,.055)
# Broad clipped corners; only small, deterministic deformations, no surface noise.
for v in stone.data.vertices:
    v.co.x += .012*math.sin(v.index*2.4); v.co.y += .009*math.cos(v.index*1.7)
origin(stone,(0,0,0)); stone['nominal_dimensions_m']='0.52 x 0.34 x 0.27'; stone['purpose']='Foundation/chimney massing prototype'
beam_o=bowed_beam('SM_Beam_Vertical_A',(0,0,0),(0,0,2.4),.18,col,mat,.026)
beam_o['purpose']='Hand-cut timber prototype; local Z follows grain'
verts=[]; faces=[]
for j in range(5):
    y=j*.14
    for i in range(9):
        x=(i/8-.5)*.34
        z=.035*math.cos((i/8-.5)*math.pi)+.016*(1-j/4)**2
        verts.append((x,y,z))
for j in range(4):
    for i in range(8):
        k=j*9+i; faces.append((k,k+1,k+10,k+9))
tile=mesh('SM_RoofTile_A',verts,faces,col,mat)
m=tile.modifiers.new('Tile physical thickness','SOLIDIFY'); m.thickness=.035
m=tile.modifiers.new('Soft lip','BEVEL');m.width=.012;m.segments=3
tile['pivot']='Centre of lower lip; local +Y uphill';tile['purpose']='Prototype only. Use shared mesh rows after silhouette checkpoint.'
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
print('MODULES_SAVED',blend)
