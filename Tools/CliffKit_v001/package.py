"""Create immutable, byte-hashed release AFTER Blender source QA. Never overwrites a release."""
import json,hashlib,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SOURCE=ROOT/'Source/Environment/CliffKit/v001';RELEASE=ROOT/'Releases/CliffKit/v001'
assert not RELEASE.exists(),'Immutable release already exists; publish a new version'
qa=json.loads((SOURCE/'QA/geometry.json').read_text());assert qa['status']=='PASS'
assert (SOURCE/'QA/ARCHETYPES.jpg').is_file()
RELEASE.mkdir(parents=True)
selected=[SOURCE/'ASSET_CATALOG.json']+sorted((SOURCE/'Meshes').glob('*.fbx'))
assert len(selected)==43
for family in ('Rock_Limestone_A','Rock_Limestone_B','GrassCap_A'):
    for name in ('BaseColor','Normal_OpenGL','Roughness','AO_Approx'):selected.append(SOURCE/'Textures'/family/(name+'.png'))
files=[]
for path in selected:
    relative=path.relative_to(SOURCE);target=RELEASE/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,target)
    files.append(dict(path=relative.as_posix(),sha256=hashlib.sha256(target.read_bytes()).hexdigest(),bytes=target.stat().st_size))
sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
catalog=json.loads((SOURCE/'ASSET_CATALOG.json').read_text())
manifest=dict(asset_id='ENV_CliffKit',version='v001',status='REVIEWED_BLENDER_CANDIDATE_ISOLATED_UNITY_INTAKE',source_commit=sha,source_path=SOURCE.relative_to(ROOT).as_posix(),blender='4.4.3',export_date='2026-10-09',unit='m',pivot='toe centre; Unity Y-up +Z uphill',collider_intention='none; real gameplay terrain owns collision and navigation',unity_tested=False,files=files,files_sha256={f['path']:f['sha256'] for f in files},assets=catalog['assets'],notes='Source/QA contains 70 real Blender renders, mesh/FBX evidence and texture provenance. Unity intake and gameplay/GPU acceptance must be recorded separately. Height and MossMask preserved in source only. Cap is rigid opaque ground, not foliage wind geometry.')
(RELEASE/'release.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
print('CLIFFKIT_RELEASE',len(files),'payload files',sum(f['bytes'] for f in files),'bytes; source',sha)
