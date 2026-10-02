# Vegetation quality contract

Reference target: original cottage concept. Tree01 is NOT yet approved and is not a production-quality baseline.

Keep close-up silhouettes, bark readability and crown volume. Use texture normal detail for small bark relief; reserve geometry for roots, branching and large silhouette changes. Bark v2 includes 1024px baked base-color and tangent-normal maps, not yet validated in Unreal. Blender OpenGL normal maps may need green-channel inversion in Unreal.

Planned quality tiers (not implemented or benchmarked):
- High: close mesh, full nearby decorative grass, highest affordable shadows and indirect lighting.
- Medium: earlier LOD transitions, fewer decorative plants and shorter shadow distance.
- Low: simplified crown meshes, shorter decorative draw distance and cheaper lighting path, retaining palette and silhouettes.

Gameplay trees, resources, collision and navigation must remain identical between quality tiers and deterministic world seeds. Only decorative foliage density may change. Never remove gameplay trees through density scaling.

Before multiplying assets: consolidate leaf color materials to one foliage material, provide near/mid/far geometry, configure wind and verify transitions in Unreal. Compare fixed-camera scenes with 1, 100 and 500 trees on target hardware; record frame time, GPU memory and draw calls. Current 81,400 leaf triangles and 10 original materials are a visual prototype, not an accepted production budget. Do not promise minimum PC specs until those tests exist.
