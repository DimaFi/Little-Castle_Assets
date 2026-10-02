# Tree 01 — first approval asset

Stylized deciduous tree, inspired by the broad foliage in the settlement concept. Actual Blender geometry; preview images are Cycles renders, not generated concept art.

- `Tree_01.blend`: editable tree, preview lights, ground and camera.
- `Tree_01.fbx`: only wood and foliage, two meshes, origin at ground level.
- `build_tree.py`: reproducible generator; SEED=28. Changing seed generates variations but currently writes the same filenames, so use a new output folder for each approved variant.
- Dimensions are authored in meters; FBX applies unit conversion on import.
- Leaves are geometry, with no external texture dependencies. Use a two-sided foliage material in Unreal. Blender subsurface settings do not reproduce automatically in Unreal.
- Vertex color R stores height-based wind weight, not an implemented wind animation.

Approval prototype, not a forest-ready performance claim: 10,175 leaves / 81,400 leaf triangles plus branches; 10 color materials. Before mass placement, consolidate materials using vertex colors, add lower-detail versions, configure Unreal foliage shading and wind, then profile a representative grove. Do not duplicate thousands of this full-detail mesh without testing.

Next assets await approval of this tree's visual direction. No world generation system has been implemented.
