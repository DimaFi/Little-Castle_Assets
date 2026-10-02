# Tree 03 — textured hero tree

Open `Tree_03_Master.blend` for the assembled tree, birdhouse and hanging lantern.
The source textures are packed into this Blender file. Original Tree_01/Tree_02,
Mat textures and original prop models are preserved.

The foliage uses six individual leaf shapes from T_Foliage_BaseColor with curved
surfaces and alpha clipping. Bark uses Bark_BaseColor / Bark_Normal, with shallow
geometric displacement and branch-oriented UVs. The birdhouse and lantern stay
separate objects; their individual FBX exports have local attachment origins.

## Geometry

| Level | Trunk triangles | Foliage triangles | Total |
| --- | ---: | ---: | ---: |
| LOD0 | 62,824 | 62,400 | 125,224 |
| LOD1 | 31,412 | 31,200 | 62,612 |
| LOD2 | 12,564 | 15,600 | 28,164 |

Lower foliage levels retain whole leaves and increase leaf size to preserve crown
coverage. These are initial reduction levels, not a measured forest budget.

## Unity handoff

Import the three Tree_03_LOD FBXs as three children at the same origin and create
an LOD Group. Materials require Unity-side setup for the chosen render pipeline.
Blender lighting, node graphs and subsurface settings do not transfer through FBX.
For foliage use the supplied atlas as Base Map, alpha clipping around 0.52,
two-sided rendering, and the LeafTint vertex color if supported by your shader.
For bark use the supplied base color and normal texture (normal import type),
with high roughness / low smoothness. Do not interpret roughness as smoothness.
The emissive lantern uses a warm amber color. Its small preview light is not
included in the standalone prop FBX.

No Unity project, render pipeline, wind shader, LOD transition profiling or target
hardware performance has been validated. A very distant billboard/impostor is
not included. The hero LOD prioritizes the requested detailed close view.
