StoneWall_A — PBR texture set for CozySettlement / Unity
=========================================================

CORE MAPS (2048x2048 PNG)
1. StoneWall_A_BaseColor_2048.png
2. StoneWall_A_Normal_2048.png
3. StoneWall_A_AO_2048.png
4. StoneWall_A_Roughness_2048.png
5. StoneWall_A_Height_2048.png

Material intent
---------------
Stylized medieval gray-beige stone for city walls, towers and defensive structures.
Designed as a repeating/tileable material so the same material can be reused across
1 m / 2 m wall modules, pillars, end pieces and archer towers.

Unity import
------------
BaseColor:
- Texture Type: Default
- sRGB (Color Texture): ON
- Wrap Mode: Repeat

Normal:
- Texture Type: Normal map
- Wrap Mode: Repeat
- If lighting appears inverted in your specific shader/pipeline, flip the green/Y channel.

AO:
- Texture Type: Default
- sRGB: OFF
- Wrap Mode: Repeat

Roughness:
- Texture Type: Default
- sRGB: OFF
- Wrap Mode: Repeat
- NOTE: Unity URP/HDRP materials often use Smoothness rather than Roughness.
  Smoothness = 1 - Roughness. Codex can invert this map or pack it into the shader's
  expected channel.

Height:
- Texture Type: Default
- sRGB: OFF
- Wrap Mode: Repeat
- Use subtly. It is intended for parallax/displacement-capable shaders, not to replace
  the actual silhouette geometry of large stones.

Metallic
--------
No metallic map is required for ordinary stone. Set Metallic = 0 in the material.
This is intentional, so the core set stays at five maps.

Recommended starting scale
--------------------------
Start around 1 texture tile per ~1.5–2.0 metres of wall and adjust by eye so the
stone size matches the wall concept art.

Important for Codex/Astra
-------------------------
- Reuse this ONE material across the modular wall set.
- Do not bake separate unique textures for each 1 m / 2 m piece.
- Keep UV density consistent on all wall, pillar and tower meshes.
- Do not rely on the material to create the large block silhouette; major stone forms,
  battlements and edges should remain geometry.
- The wall-building algorithm places rigid modular pieces along a curve. The material
  must therefore remain independent of module length and orientation.

Files are prepared as a practical game-ready PBR set.
