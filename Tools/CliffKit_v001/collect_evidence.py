"""Copy bounded Unity evidence from a supplied checkout; no authoring code in game build."""
import argparse,json,shutil,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image,ImageDraw
ap=argparse.ArgumentParser();ap.add_argument('--game',type=Path,required=True);args=ap.parse_args()
ROOT=Path(__file__).resolve().parents[2];game=args.game.resolve();logs=game/'Logs';dest=game/'docs/reports/cliff-kit-v001-evidence';dest.mkdir(parents=True,exist_ok=True)
for name in ('CliffKitEditMode.xml','CliffKitPlayMode.xml','CliffKitImport.json','CliffKitTerrainAudit.json'):
    shutil.copyfile(logs/name,dest/name)
for path in logs.glob('CliffKit_*.png'):shutil.copyfile(path,dest/path.name)
catalog=json.loads((ROOT/'Source/Environment/CliffKit/v001/ASSET_CATALOG.json').read_text())
for mode in ('Day','Night'):
    sheet=Image.new('RGB',(1600,1328),(25,29,34));draw=ImageDraw.Draw(sheet)
    for i,entry in enumerate(catalog['assets']):
        x=(i%4)*400;y=(i//4)*332
        im=Image.open(logs/f'CliffKit_{entry["id"]}_{mode}.png').resize((400,300),Image.Resampling.LANCZOS)
        sheet.paste(im,(x,y+32));draw.text((x+12,y+10),entry['id'],fill='white')
    sheet.save(dest/f'Unity_{mode}_Contact.jpg',quality=92)
summary={}
for name in ('CliffKitEditMode.xml','CliffKitPlayMode.xml'):
    node=ET.parse(dest/name).getroot();summary[name]={k:node.attrib.get(k) for k in ('total','passed','failed','skipped','result','duration','start-time','end-time')}
summary['release_sha256']=hashlib.sha256((ROOT/'Releases/CliffKit/v001/release.json').read_bytes()).hexdigest()
summary['game_payload_sha256_pass']=True
release=json.loads((ROOT/'Releases/CliffKit/v001/release.json').read_text())
for entry in release['files']:
    payload=game/'Assets/_Game/Art/Imported/CliffKit/v001'/entry['path']
    assert hashlib.sha256(payload.read_bytes()).hexdigest()==entry['sha256'],payload
(dest/'checks.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
lines=[]
for name in ('CliffKitImport-failed-forward.log','CliffKitImport-failed-rootrotation.log','CliffKitImport.log','CliffKitReview.log'):
    lines.extend([name]+[s for s in (logs/name).read_text(encoding='utf-8',errors='replace').splitlines() if any(key in s for key in ('InvalidDataException:','CLIFFKIT_IMPORT_PASS','CLIFFKIT_DESKTOP_REVIEW','Renderer:','Vendor:','Forcing GfxDevice:','Application will terminate with return code'))])
(dest/'UnityChecks.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps(summary))
