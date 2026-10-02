# Reusable tree props

Separate models, each in its own Blender file and FBX. Authoring units are meters. No tree geometry is included.

- Birdhouse_01: pivot at rear mounting surface, Z upright, entrance faces Blender -Y; real cut entrance, hollow body, perch and mounting plank. Height about 0.60 m.
- Lantern_01: pivot at top of hanging eye, Z upright. Height about 0.45 m. Hang under a branch, beam or bracket; cord/chain is deliberately separate from this reusable asset.
- Models use UVs and color materials without external textures. Preview lighting is not exported. Unreal glass/emission material requires explicit setup; FBX does not guarantee transmission/emission transfer.
- build_props.py regenerates both models and previews. It replaces only these generated outputs.

Compared with the small original concept details, these are reconstructed interpretations, not exact recovered source geometry. Front three-quarter renders inspected; Unreal import, LODs and collision not yet validated. No automatic replacement of tree-mounted props has been performed.
