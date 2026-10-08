"""Static geometry interference test for rigid gates rotating inward (+Unity X)."""
import bpy, math, sys, json
from pathlib import Path
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
HERE=Path(__file__).resolve().parent

def bvh(objects, matrix=None):
    verts=[];faces=[]
    for ob in objects:
        me=ob.data;me.calc_loop_triangles();offset=len(verts)
        verts.extend((matrix @ v.co if matrix is not None else v.co.copy()) for v in me.vertices)
        faces.extend(tuple(offset+i for i in p.vertices) for p in me.loop_triangles)
    return BVHTree.FromPolygons(verts,faces,all_triangles=True,epsilon=1e-7)

def sweep(x, lod=0, step=1):
    gate=bvh([bpy.data.objects[f'SM_Wall_Gatehouse_A_Stone_LOD{lod}']])
    collisions=[]
    for side,z,sign in [('Left',-1.04,1),('Right',1.04,-1)]:
        parts=[bpy.data.objects[f'SM_Wall_GateLeaf_{side}_A_{part}_LOD{lod}'] for part in ['Timber','Iron']]
        for i in range(round(90/step)+1):
            angle=i*step
            matrix=Matrix.Translation(Vector((x,-z,0))) @ Matrix.Rotation(math.radians(angle*sign),4,'Z')
            overlap=gate.overlap(bvh(parts,matrix))
            if overlap:collisions.append({'side':side,'angle':angle,'triangle_pairs':len(overlap)})
    return {'hinge_x':x,'lod':lod,'angle_step_degrees':step,'collisions':collisions}

if __name__=='__main__':
    bpy.ops.wm.open_mainfile(filepath=str(HERE.parent/'v004/Wall_Fortifications.blend'))
    results=[sweep(x,0,1) for x in [.4215707778930664,.57,.60]]
    (HERE/'QA/gate_sweep_diagnostic.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    for r in results:print('SWEEP',r['hinge_x'],len(r['collisions']),r['collisions'][:5])
