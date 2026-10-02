"""Read-only inventory of Mat; thumbnails are diagnostic, not game textures."""
from pathlib import Path
import json
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
MAT = ROOT.parents[1] / 'Mat'
groups = []
for folder in sorted(p for p in MAT.iterdir() if p.is_dir()):
    files = []
    for p in sorted(folder.rglob('*')):
        if p.is_file():
            entry = {'path': str(p.relative_to(MAT)), 'bytes': p.stat().st_size}
            try:
                with Image.open(p) as im:
                    entry.update(size=list(im.size), mode=im.mode)
            except Exception:
                pass
            files.append(entry)
    groups.append({'folder': folder.name, 'files': files})
(ROOT / 'QA/material_inventory.json').write_text(json.dumps(groups, ensure_ascii=False, indent=2), encoding='utf-8')
names = ['T_Timber','T_Plaster','T_FieldStone','T_ChimneyStone','RoofTile','DoorWood','Shutters','Logs_Bark','Bark','T_Foliage']
sheet = Image.new('RGB', (1250, 540), '#272b2e')
d = ImageDraw.Draw(sheet)
for i, name in enumerate(names):
    p = next((MAT / name).glob('*BaseColor.png'))
    with Image.open(p) as src:
        src.thumbnail((238, 238))
        x, y = (i % 5)*250+6, (i // 5)*270+25
        sheet.paste(src.convert('RGB'), (x,y))
        d.text((x,y-18), name, fill='white')
sheet.save(ROOT / 'QA/material_contact_sheet.jpg')
print('Inventoried', sum(len(g['files']) for g in groups), 'files in', len(groups), 'folders')
