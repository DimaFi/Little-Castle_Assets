"""Publish validated well/bucket revisions and update existing Asset Book IDs."""
import json,runpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];PROJECT=ROOT.parents[1]
reports=json.loads((ROOT/'QA/well_bucket_v020_readback.json').read_text(encoding='utf-8'))
assert len(reports)==4 and all(r['packed_images'] and r['camera_saved'] and all(not c['issues'] for c in r['checks']) for r in reports)
names=['SM_Well_A','SM_Bucket_A'];ids=['PROP_Well_A','PROP_Bucket_A']
p=PROJECT/'AssetsDatabase/AssetBook.json';book=json.loads(p.read_text(encoding='utf-8'));byid={a['id']:a for a in book['assets']}
assert all(n in byid for n in ['MAT_Cottage_HempRope_A','MAT_Cottage_ForgedIron_A','MOD_Cottage_Courtyard_A','MOD_Cottage_Yard_Kit_A'])
for name,asset_id in zip(names,ids):
    asset=byid[asset_id];old=asset['path']+'/'+asset['source_file']
    new=f'Art/House_Cottage_A/Source/Yard/v004/Modules/{name}'
    if asset['path']!=new:asset.setdefault('source_history',[]).append(old)
    asset.update(path=new,source_file=name+'.blend',status='Ready',can_reuse=True,
                 notes='Existing model upgraded in place (stable ID): UV/materials, packed maps. Well clay thickness restored; bucket handle seated. Blender reusable; engine baking/LOD/collision/lightmap pending.')
    mats=['MAT_T_Timber','MAT_Cottage_ForgedIron_A']
    if name=='SM_Well_A':mats=['MAT_T_Timber','MAT_T_FieldStone','MAT_RoofTile','MAT_Cottage_HempRope_A']
    asset['materials']=mats;asset['dependencies']=sorted(set(asset.get('dependencies',[])+mats))
    asset['textures']=['TEX_T_Timber']+(['TEX_T_FieldStone','TEX_RoofTile'] if name=='SM_Well_A' else [])
    if name=='SM_Well_A':asset['dependencies'].append('PROP_LogStack_A') # reused cut-end shader
    folder=ROOT/'Source/Yard/v004/Modules'/name
    (folder/'README_RU.md').write_text(f'''# {name} — v004

Asset Book ID: {asset_id}. Обновление существующей модели, не новый вариант.
Самостоятельная сцена Blender 4.4.3, метры, Z вверх, фронт −Y. Numpad 0 — камера.
Карты встроены. Материалы и UV0 готовы для просмотра; lightmap/LOD/коллизии
и игровой экспорт не выполнены. Процедурные материалы нужно запекать.
Студию не экспортировать. Источник в сборке — локальная коллекция;
изменения отдельного файла переносятся в сборку явно.
Описание: Docs/16_Well_Bucket_AssetBook_RU.md в корне House_Cottage_A.
''',encoding='utf-8')
yard_names=['Woodshed','LogStack','Well','Barrel','Bucket','WoodBench','WoodTable','FlowerBox','Pot','Crate','FenceBay','Gate','StoneWall','Stump_Axe','Birdhouse','Signpost','Wheelbarrow']
yard_ids=[('MOD_' if n in ['FenceBay','Gate','StoneWall'] else 'PROP_')+n+'_A' for n in yard_names]
byid['MOD_Cottage_Yard_Kit_A']['dependencies']=yard_ids
byid['MOD_Cottage_Courtyard_A']['dependencies']=['BLD_House_Cottage_A']+yard_ids
helper=runpy.run_path(str(PROJECT/'Scripts/asset_book.py'),run_name='asset_book_helpers')
helper['rebuild_used_by'](book);helper['save'](book)

p=ROOT/'CURRENT.json';d=json.loads(p.read_text(encoding='utf-8'))
d.update(assembly='Source/Assembly/v020/Cottage_Courtyard.blend',yard_kit='Source/Yard/v004/Cottage_Yard_Kit.blend',
         yard_material_notes='Docs/16_Well_Bucket_AssetBook_RU.md',stage='four yard modules textured; stable IDs and dependencies recorded in Asset Book; other props and engine preparation pending')
d['yard_module_overrides'].update({n:f'Source/Yard/v004/Modules/{n}/{n}.blend' for n in names})
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
p=ROOT/'README.md';s=p.read_text(encoding='utf-8')
s=s.replace('**Актуальная сборка v019: добавлены материалы дровника и дров.','**Актуальная сборка v020: материалы колодца и ведра; изменения учтены в Asset Book.')
s=s.replace('Source/Assembly/v019/Cottage_Courtyard.blend','Source/Assembly/v020/Cottage_Courtyard.blend').replace('Source/Yard/v003/Cottage_Yard_Kit.blend','Source/Yard/v004/Cottage_Yard_Kit.blend').replace('Renders/Checkpoint_14/v019/Courtyard_Hero.png','Renders/Checkpoint_15/v020/Courtyard_Hero.png')
s+='\n## Колодец и ведро v020\n\nМатериалы готовы у четырёх дворовых модулей. Колодец и ведро — Yard/v004/Modules,\nдровник и дрова — Yard/v003/Modules; ещё 13 модулей — Yard/v002/Modules.\nАктуальные пути есть в CURRENT.json, каталоге и Asset Book проекта.\n[Описание этапа](Docs/16_Well_Bucket_AssetBook_RU.md).\n'
p.write_text(s,encoding='utf-8')
p=ROOT/'Docs/07_Module_Catalog_RU.md';s=p.read_text(encoding='utf-8')
for i,n in enumerate(names):
    s=s.replace(f'../Source/Yard/v002/Modules/{n}/{n}.blend',f'../Source/Yard/v004/Modules/{n}/{n}.blend').replace(f'../Renders/Yard/v002/{n}.png',f'../Renders/Checkpoint_15/v020/{n}.png')
    lines=s.splitlines()
    for j,line in enumerate(lines):
        if f'[{n}]' in line:
            fields=line.split('|');fields[3]=f" {reports[i+2]['checks'][0]['triangles']:,} ";lines[j]='|'.join(fields)
    s='\n'.join(lines)+'\n'
p.write_text(s,encoding='utf-8')
p=ROOT/'Docs/03_Progress_RU.md';s=p.read_text(encoding='utf-8')
s+='\n## v020 — колодец, ведро и Asset Book\n\nПереиспользованы существующие модели и материалы. Добавлен материал верёвки;\nисправлены толщина/конёк колодца и посадка ручки ведра. Сохранены сборка,\nгалерея и два отдельных модуля. Стабильные ID и зависимости обновлены в Asset Book.\n'
p.write_text(s,encoding='utf-8')
(ROOT/'Docs/CONTINUE_HERE_RU.md').write_text('''# Точка продолжения — v020

Сборка: Source/Assembly/v020/Cottage_Courtyard.blend. Дом отдельно остаётся v018.
Галерея: Source/Yard/v004/Cottage_Yard_Kit.blend.
Материалы готовы у четырёх предметов: дровник, дрова, колодец, ведро.
Пути отдельных модулей брать из CURRENT.json с учётом yard_module_overrides.
Подробности: Docs/16_Well_Bucket_AssetBook_RU.md.

В проекте действует AGENTS.md: ДО новых ассетов искать через
Scripts/asset_book.py search; AssetBook.json — источник истины. Публиковать
ASSET REUSE CHECK, переиспользовать найденное, регистрировать действительно
новые ассеты; при обновлении сохранять ID и обновлять путь/зависимости. Выполнять sync.

Следующая небольшая партия — стол, скамейка и ящик: использовать готовое дерево,
проверить направление волокон, обновить сборку/галерею/отдельные файлы и Asset Book.
Затем остальные 10 серых дворовых модулей и фонарь дома. Игровая подготовка,
земля и растительность окружения остаются впереди. Старые издатели документации
не запускать поверх текущих ссылок.
''',encoding='utf-8')
print('WELL_DOCUMENTATION_COMPLETE')
