# Reuse check — 2026-10-02

Inspected the existing CozySettlement AssetBook and the actual render/source
documentation for `MOD_StoneWall_A` in `Art/House_Cottage_A/Source/Yard/v002`.
It is a three-course low garden wall: no battlements, pillar, cap, final UV,
LOD or game export. Reusing its dimensions/mesh would not satisfy this kit.
It remains unchanged. This new kit uses distinct stable IDs.

Initial masonry material candidate: `MAT_T_ChimneyStone`; inspected its maps
and cottage material setup. User subsequently explicitly selected
`CozySettlement/Mat/StoneWall_A_Unity`. The final models reuse that entire
texture suite byte-for-byte, with no unique texture baking. Intermediate
ChimneyStone input copies are not included in the release.

The existing art repository skeleton has not yet migrated its old 125-record
catalog. Its new AssetBook registers only this newly authored kit and its
new material/texture IDs; later migration must MERGE existing IDs, not replace
this new catalog. The original CozySettlement catalog is unchanged.

No Unity import, runtime rewrite, old-asset replacement, commit or push is
part of this asset authoring pass. Local Git LFS filters and pre-push hook
were inspected and are already installed.
