"""Publish immutable reviewed art, update existing scoped Unity copies with backups."""
from pathlib import Path
import hashlib, json, shutil, subprocess
HERE=Path(__file__).resolve().parent
ART=HERE.parents[3];GAME=ART.parent/'Little-Castle'
RELEASE=ART/'Releases/Wall_Stone_Modular/v005'
TARGET=GAME/'Assets/_Game/Art/Imported/TerrainStarter_v001'
BACKUP=GAME/'Temp/Fortifications-v005-backup'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def backup(path):
    dest=BACKUP/path.relative_to(GAME)
    if path.is_file() and not dest.exists():
        dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dest)

qa=json.loads((HERE/'QA/export_validation.json').read_text())
assert qa['status']=='PASS' and sha(HERE/'Wall_Fortifications.blend')==qa['source_sha256']
assert json.loads((HERE/'QA/gate_sweep.json').read_text())['status']=='PASS'
source=HERE/'Input/UserEdits_2026-10-06.blend'
assert sha(source)==sha(HERE.parent/'v004/Wall_Fortifications.blend'),'User source changed again; inspect new edits first'
paths=list((HERE/'Meshes').glob('*.fbx'))+list((HERE/'Textures').glob('*.png'))
paths += [HERE/'Textures/material-bindings.json',HERE/'Connections.json',HERE/'README_RU.md']
paths += list((HERE/'Preview').glob('*.png'))+[HERE/'QA/geometry_report.json',HERE/'QA/export_validation.json',HERE/'QA/gate_sweep.json']
files=[]
for p in paths:
    relative=p.relative_to(HERE);dest=RELEASE/relative;dest.parent.mkdir(parents=True,exist_ok=True)
    if dest.exists():assert sha(dest)==sha(p),f'Immutable release conflict: {dest}'
    else:shutil.copy2(p,dest)
    files.append({'path':relative.as_posix(),'sha256':sha(dest),'bytes':dest.stat().st_size})
manifest={'version':'v005','status':'AUTHORED_QA_PASS','source':HERE.relative_to(ART).as_posix(),
          'source_sha256':qa['source_sha256'],'manual_input_sha256':sha(source),
          'source_commit':subprocess.check_output(['git','-c',f'safe.directory={ART.as_posix()}','-C',str(ART),'rev-parse','HEAD'],text=True).strip(),
          'source_worktree_dirty':True,'blender_version':'4.4.3','export_date':'2026-10-06',
          'units':'metres','up':'Y','pivot':'base-centre; gate leaves at hinge',
          'collider_intention':'UCX box guides only; exclude from rendering',
          'geometry_report':'QA/geometry_report.json','preview':'Preview/Gate_Interior_90.png','files':files}
mp=RELEASE/'release.json'
if mp.exists():assert json.loads(mp.read_text())==manifest,'Release manifest conflict'
else:mp.write_text(json.dumps(manifest,indent=2),encoding='utf-8')
for p in TARGET.rglob('*.prefab'):
    if p.stem.startswith(('SM_Wall_','SM_ArcherTower_')):backup(p)
for p in TARGET.glob('*.unity'):backup(p)
backup(TARGET/'provenance.json');backup(TARGET/'Connections.json')
provenance=json.loads((TARGET/'provenance.json').read_text())
entries={e['target']:e for e in provenance['files']}
updated=[]
for entry in files:
    relative=entry['path']
    if relative.startswith('Meshes/'):target_relative=relative.replace('Meshes/','Models/',1)
    elif relative=='Connections.json' or relative.startswith('Textures/'):target_relative=relative
    else:continue
    src=RELEASE/relative;dest=TARGET/target_relative
    if not dest.exists() or sha(src)!=sha(dest):
        backup(dest);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest);updated.append(target_relative)
    entries[target_relative]={'source':src.relative_to(ART.parent).as_posix(),'target':target_relative,'sha256':sha(src),'bytes':src.stat().st_size}
provenance['files']=list(entries.values());provenance['fortifications_version']='v005'
(TARGET/'provenance.json').write_text(json.dumps(provenance,indent=2),encoding='utf-8')
(HERE/'QA/import_copy.json').write_text(json.dumps({'updated':updated,'backup':str(BACKUP),'unity_editor_validation':'pending'},indent=2),encoding='utf-8')
print('WALL_RELEASE_AND_EXISTING_IMPORT_UPDATED',len(updated),str(BACKUP))
