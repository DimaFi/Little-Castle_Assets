"""Validate local catalog records and generate the readable inventory.
Does not invent IDs or migrate the still-external legacy catalog.
"""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
book=json.loads((ROOT/'AssetBook/AssetBook.json').read_text(encoding='utf-8'))
assets=book['assets'];ids=[a['id'] for a in assets]
assert len(ids)==len(set(ids)),'Duplicate asset IDs'
lines=['# Little Castle Asset Book','',book.get('migration_note',''),'','| ID | Type | Export | Status |','|---|---|---|---|']
for a in assets:
    export=ROOT/a['path']/a['source_file']
    assert export.is_file(),export
    if a.get('editable_source'):assert (ROOT/a['editable_source']).is_file()
    assert all(d in ids for d in a['dependencies']),(a['id'],'unresolved dependency')
    relative=export.relative_to(ROOT).as_posix()
    lines.append(f"| {a['id']} | {a['category']} | [{a['source_file']}](../{relative}) | {a['status']} |")
(ROOT/'AssetBook/AssetBook.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('ASSET_BOOK_VALIDATED',len(assets),'records; all files and dependencies resolved')
