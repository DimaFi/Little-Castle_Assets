# Visual review — 2026-10-02

Reviewed actual Blender renders of the exported source meshes, using the
user-selected StoneWall_A_Unity maps. This is asset QA, not Unity acceptance.

- Kit_Overview: all four stone modules and the separate neutral cloth/bracket
  are present. Low wall silhouette, three/two merlons and higher capped pillar
  remain readable. No trees, ground mesh, props or lights enter the FBX.
- Wall_Modular_Preview: straight run plus a gently bending chain of six rigid
  modules with 5-degree yaw increments and structural pillars. Camera framing
  includes the complete wall. Inward-tapered quiet ends remove the dark
  coplanar-overlap stripe observed in the first export iteration.
- QA_Mixed_and_Sharp: 2m-to-1m/cap chain and hand-assembled pillar-covered
  90-degree corner remain joined. The scene is a geometry test, not a runtime
  WallPathLayoutUtility capture.
- Stone_and_Banner_Closeup: neutral cloth hangs outside the pillar with no
  visible stone-through-cloth conflict. Mount remains a separate model.
- QA_LOD_Comparison: same dimensions and major merlon silhouette; small bevels
  and body relief disappear at LOD2 as intended. Tune distances in Unity.
- QA_Player_Colours: blue, red, green and ochre on copies of the same cloth.
- QA_Banner_PNG_LODs: asymmetric F and four-colour diagnostic PNG is upright
  and unmirrored on the front at every LOD. Diagnostic material is preview-only.

Remaining integration limits: exact texture-phase matching at arbitrary overlap
is not promised; subtle seams and texture repetition remain visible close up.
Source texture contains painted stone variation/moss and is preserved as chosen.
Unity import normals, lighting, LOD distances, collision removal/BoxCollider,
actual algorithm tower gaps, Sharp corner placement and PNG compositor must be
checked when the kit is integrated. No game-ready scene claim is made here.

Disposition: acceptable first authored asset set for delivery and Unity
integration, subject to the user's visual review. No existing assets replaced.
# Superseded by user review

The user rejected this version for flat masonry and poor texture appearance.
The earlier inspection below is historical, NOT visual acceptance. Continue in v002.
