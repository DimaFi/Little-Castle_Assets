"""Copy a validated local art release; never imports Unity or overwrites a release.
Run with bundled Blender Python after build + validate + visual inspection.
"""
import json, shutil, hashlib, subprocess
from pathlib import Path

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[3]
DEST=REPO/'Releases/Wall_Stone_Modular/v001'

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    qa=json.loads((HERE/'QA/export_validation.json').read_text(encoding='utf-8'))
    assert qa['status']=='PASS'
    assert not DEST.exists(),'Release already exists: author a new version instead of overwriting.'
    assert (HERE/'QA/visual_review.md').exists(),'Record visual inspection first.'
    for folder in ['Meshes','Textures','Preview','QA']:(DEST/folder).mkdir(parents=True,exist_ok=True)
    for p in (HERE/'Meshes').glob('*.fbx'):shutil.copy2(p,DEST/'Meshes'/p.name)
    for p in (HERE/'Textures').glob('StoneWall_A_*_2048.png'):shutil.copy2(p,DEST/'Textures'/p.name)
    for name in ['README_Unity.txt','material-bindings.json']:shutil.copy2(HERE/'Textures'/name,DEST/'Textures'/name)
    for p in (HERE/'Preview').glob('*.png'):shutil.copy2(p,DEST/'Preview'/p.name)
    for name in ['export_validation.json','geometry_report.json','visual_review.md']:
        shutil.copy2(HERE/'QA'/name,DEST/'QA'/name)
    readme=(HERE/'README_RU.md').read_text(encoding='utf-8')
    readme=readme.replace('(Wall_Stone_Modular.blend)',
        '(../../../Source/Architecture/Wall_Stone_Modular/v001/Wall_Stone_Modular.blend)')
    (DEST/'README_RU.md').write_text(readme,encoding='utf-8')
    manifest={
        'asset_id':'Wall_Stone_Modular','version':'v001','date':'2026-10-02',
        'status':'asset_export_validated_unity_integration_pending',
        'source':str(HERE.relative_to(REPO)/'Wall_Stone_Modular.blend').replace('\\','/'),
        'source_commit':None,'source_commit_note':'New local source files are not committed or pushed.',
        'repository_base_commit':subprocess.check_output(['git','-c','safe.directory='+REPO.as_posix(),'-C',str(REPO),'rev-parse','HEAD'],text=True).strip(),
        'source_sha256':digest(HERE/'Wall_Stone_Modular.blend'),
        'generator_sha256':digest(HERE/'build_wall_kit.py'),
        'blender':'4.4.3','units':'metres','up_axis':'Y','length_axis':'Z',
        'stone_pivot':'base centre','banner_pivot':'top centre',
        'colliders':'four 12-triangle UCX reference boxes; explicitly create Unity BoxCollider and hide/remove proxy renderer',
        'material':'StoneWall_A_Unity selected by user; original PNG files unchanged',
        'preview':'Preview/Kit_Overview.png',
        'lods':{row['file']:[x['triangles'] for x in row['roundtrip_lods']] for row in qa['exports']},
        'files':[]}
    for p in sorted(DEST.rglob('*')):
        if p.is_file():manifest['files'].append({'path':p.relative_to(DEST).as_posix(),'bytes':p.stat().st_size,'sha256':digest(p)})
    (DEST/'release.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    # Re-read copied files; the release is a copy, not a live dependency on Source.
    for row in manifest['files']:assert digest(DEST/row['path'])==row['sha256']
    print('RELEASE_COPY_VERIFIED',DEST,len(manifest['files']))

if __name__=='__main__':main()
