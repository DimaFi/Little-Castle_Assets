"""Create an immutable, locally reviewed export package. Does not import to Unity."""
import json, shutil, hashlib, subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
TARGET=ROOT/'Releases/Bridge_Stone_A/v001'
qa=json.loads((HERE/'QA/roundtrip_report.json').read_text())
assert qa['passed']
assert not TARGET.exists(), 'Release already exists; create a new source version.'
TARGET.mkdir(parents=True)
for folder in ['Meshes','Textures','QA','Preview']:
    shutil.copytree(HERE/folder,TARGET/folder)
for name in ['README.md','bridge-site.json','bridge_contract.py']:
    shutil.copy2(HERE/name,TARGET/name)
files={str(p.relative_to(TARGET)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest()
       for p in TARGET.rglob('*') if p.is_file()}
head=subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,capture_output=True,text=True)
manifest=dict(asset_id='ENV_Bridge_Stone_A',version='v001',date='2026-10-08',
    status='Source/FBX reviewed; Unity integration pending',unity_tested=False,
    source='Source/Architecture/Bridge_Stone_A/v001/Bridge_Stone_A.blend',
    source_commit=head.stdout.strip() if head.returncode==0 else None,
    source_uncommitted=True,source_sha256=hashlib.sha256((HERE/'Bridge_Stone_A.blend').read_bytes()).hexdigest(),
    blender_version='4.4.3',units='metres',axes='Y-up; road Z; river X',
    pivot='Crossing centre, approach grade Y=0',
    lod_triangles=[qa[f'bridge_lod{i}_triangles'] for i in range(3)],
    textures=list(files.keys()),
    collider_intent='COL_Bridge_A: 286 triangles, static non-convex, near gameplay only',
    preview='Preview/Bridge_Hero.png',files_sha256=files)
manifest['textures']=[p for p in files if p.startswith('Textures/')]
(TARGET/'release.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print('BRIDGE_PACKAGE_READY',str(TARGET),len(files),'files')
