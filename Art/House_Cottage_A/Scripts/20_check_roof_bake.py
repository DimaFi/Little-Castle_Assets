"""Regression: hidden prototype must retain applied thickness and bevel."""
import ast,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from kit_geometry import *
ROOT=Path(__file__).resolve().parents[1]
tree=ast.parse((ROOT/'Scripts/07_build_roof_tiles.py').read_text(encoding='utf-8'))
function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='bake')
exec(compile(ast.Module(body=[function],type_ignores=[]),'<roof bake>','exec'))
bpy.ops.wm.read_factory_settings(use_empty=True)
c=collection('Hidden prototypes');c.hide_viewport=True;c.hide_render=True
o=mesh('RegressionTile',[(-.16,0,0),(.16,0,0),(.16,.5,0),(-.16,.5,0)],[(0,1,2,3)],c,grey_material())
m=o.modifiers.new('Thickness','SOLIDIFY');m.thickness=.035;m.offset=-1
m=o.modifiers.new('Lip','BEVEL');m.width=.006;m.segments=1
bake(o)
bm=bmesh.new();bm.from_mesh(o.data)
stats={'vertices':len(bm.verts),'faces':len(bm.faces),'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),
       'volume':abs(bm.calc_volume()),'remaining_modifiers':len(o.modifiers),
       'prototype_collection_still_hidden':c.hide_viewport and c.hide_render}
assert stats['nonmanifold_edges']==0 and stats['volume']>.004 and not o.modifiers,stats
assert stats['prototype_collection_still_hidden'] and list(o.users_collection)==[c],stats
assert min(v.co.z for v in bm.verts)<-.034 and max(v.co.z for v in bm.verts)<1e-6,stats
bm.free();(ROOT/'QA/roof_bake_regression.json').write_text(json.dumps(stats,indent=2),encoding='utf-8')
print('ROOF_BAKE_REGRESSION_PASSED',stats,flush=True)
