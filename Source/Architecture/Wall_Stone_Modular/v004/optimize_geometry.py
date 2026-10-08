"""Conservative internal-face culling; never moves a surviving vertex or UV.

Each occluder must be a closed, consistently oriented connected solid.
Its inward half-space intersection is a conservative subset of that solid.
A triangle is removed only when all three vertices are strictly inside it.
No ground-facing, exposed, merely back-facing or intersecting face is removed.
"""
import bmesh
import numpy as np


def components(mesh):
    parent=list(range(len(mesh.vertices)))
    def root(i):
        while parent[i]!=i:
            parent[i]=parent[parent[i]]; i=parent[i]
        return i
    for e in mesh.edges:
        a,b=map(root,e.vertices); parent[a]=b
    groups={}
    for p in mesh.polygons:
        groups.setdefault(root(p.vertices[0]),[]).append(p.index)
    return list(groups.values())


def optimize(parts):
    solids=[]; data=[]
    for ob in parts:
        me=ob.data
        xyz=np.array([v.co[:] for v in me.vertices],dtype=np.float64)
        faces=np.array([p.vertices[:] for p in me.polygons],dtype=np.int32)
        assert faces.shape[1]==3
        pts=xyz[faces]; data.append((ob,pts))
        for ids in components(me):
            fs=faces[ids]; edges={}
            for f in fs:
                for a,b in zip(f,np.roll(f,-1)):
                    k=(min(a,b),max(a,b)); edges.setdefault(k,[]).append(a<b)
            if any(len(v)!=2 or v[0]==v[1] for v in edges.values()):continue
            cp=pts[ids]; normals=np.cross(cp[:,1]-cp[:,0],cp[:,2]-cp[:,0])
            lengths=np.linalg.norm(normals,axis=1)
            if min(lengths)<1e-12:continue
            volume=np.sum(np.einsum('ij,ij->i',cp[:,0],np.cross(cp[:,1],cp[:,2])))/6
            if volume<=1e-10:continue
            normals/=lengths[:,None]
            offsets=np.einsum('ij,ij->i',normals,cp[:,0])
            # Duplicate coplanar planes only waste time, without changing the test.
            planes=np.unique(np.round(np.column_stack((normals,offsets)),9),axis=0)
            solids.append((cp.min(axis=(0,1)),cp.max(axis=(0,1)),planes[:,:3],planes[:,3]))
    stats=[]
    for ob,pts in data:
        before=(len(ob.data.vertices),len(ob.data.polygons))
        removed=np.zeros(len(pts),dtype=bool)
        lower=pts.min(axis=1); upper=pts.max(axis=1)
        for lo,hi,n,d in solids:
            candidates=np.flatnonzero((~removed)&np.all(lower>lo+1e-6,axis=1)&np.all(upper<hi-1e-6,axis=1))
            if not len(candidates):continue
            distances=np.einsum('tvj,pj->tvp',pts[candidates],n)-d
            removed[candidates[np.all(distances < -1e-6,axis=(1,2))]]=True
        bm=bmesh.new();bm.from_mesh(ob.data);bm.faces.ensure_lookup_table()
        bmesh.ops.delete(bm,geom=[bm.faces[i] for i in np.flatnonzero(removed)],context='FACES')
        bm.to_mesh(ob.data);bm.free();ob.data.update()
        stats.append({'name':ob.name,'vertices_before':before[0],'vertices_after':len(ob.data.vertices),
                      'triangles_before':before[1],'triangles_after':len(ob.data.polygons),
                      'removed_fully_internal_triangles':int(removed.sum())})
    return stats


def optimize_assets(assets):
    report={'method':'Strict interior half-space culling; surviving positions and UVs unchanged','parts':[]}
    for a in assets.values():
        for parts in a['levels']:report['parts'].extend(optimize(parts))
    return report
