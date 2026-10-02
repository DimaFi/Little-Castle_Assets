"""Publish the first yard-material batch after readback of four files."""
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
reports=json.loads((ROOT/'QA/yard_materials_v019_readback.json').read_text(encoding='utf-8'))
assert len(reports)==4 and all(r['packed_images'] and r['saved_camera'] and all(not c['issues'] for c in r['checks']) for r in reports)
names=['SM_Woodshed_A','SM_LogStack_A']
for name in names:assert (ROOT/'Renders/Checkpoint_14/v019'/(name+'.png')).exists()
p=ROOT/'CURRENT.json';d=json.loads(p.read_text(encoding='utf-8'))
d.update(assembly='Source/Assembly/v019/Cottage_Courtyard.blend',yard_kit='Source/Yard/v003/Cottage_Yard_Kit.blend',
         yard_material_notes='Docs/15_Yard_Materials_Batch1_RU.md',
         stage='house v018 preserved; woodshed and logs textured in assembly v019; other yard props and lantern pending')
d.setdefault('yard_module_overrides',{}).update({n:f'Source/Yard/v003/Modules/{n}/{n}.blend' for n in names})
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for name,description in zip(names,['Дровник: деревянный каркас и доски, черепица, каменные опоры, дрова.','Штабель дров: кора и отдельный материал годовых колец на торцах.']):
    p=ROOT/'Source/Yard/v003/Modules'/name/'README_RU.md'
    p.write_text(f'''# {name} — материалы, v003

{description}

Открывать соседний {name}.blend в Blender 4.4.3. Сохранены самостоятельная
сцена, камера и студия; Numpad 0 — общий вид. Объект в коллекции {name}.
Метры, Z вверх, фронт −Y, начало координат модуля сохранено.
Карты встроены. Студию не экспортировать. UV0 предназначены для материалов,
не для lightmap. Процедурные годовые кольца нужно запечь перед игровым экспортом.
Изменения в этом файле не обновляют сборку автоматически: модуль добавлен как
локальная коллекция, поэтому переносить обновление в сборку явно.
Старая серая версия: Source/Yard/v002/Modules/{name}.
Подробности: Docs/15_Yard_Materials_Batch1_RU.md в корне House_Cottage_A.
''',encoding='utf-8')
p=ROOT/'README.md';s=p.read_text(encoding='utf-8')
s=s.replace('**Актуальная версия v018: исправлены видимость угловых стоек и примыкание черепицы к люкарне.',
            '**Актуальная сборка v019: добавлены материалы дровника и дров. Дом отдельно остаётся v018.')
s=s.replace('Source/Assembly/v018/Cottage_Courtyard.blend','Source/Assembly/v019/Cottage_Courtyard.blend')
s=s.replace('Source/Yard/v002/Cottage_Yard_Kit.blend','Source/Yard/v003/Cottage_Yard_Kit.blend')
s=s.replace('Renders/Checkpoint_13/v018/Courtyard_Hero.png','Renders/Checkpoint_14/v019/Courtyard_Hero.png')
s=s.replace('`Source/Assembly/v018`: актуальная совместная сцена.',
            '`Source/Assembly/v018`: предыдущая совместная сцена.\n- `Source/Assembly/v019`: актуальная сборка, дровник и дрова с материалами.')
s=s.replace('Фонарь и двор пока серые; экспорт ещё не готов.',
            'Дровник и дрова получили материалы в v019. Фонарь и остальные предметы двора пока серые; экспорт ещё не готов.')
marker='## Материалы двора — первая партия v019'
if marker not in s:s+='\n'+marker+'''\n
Дровник и штабель дров обновлены в `Source/Yard/v003/Modules`.
Другие 15 дворовых модулей пока брать из `Source/Yard/v002/Modules`.
Полная галерея v003 содержит все 17 модулей, из них два с материалами.
`CURRENT.json`: поле `yard_module_overrides` имеет приоритет над `yard_modules`.
[Материалы и дальнейшие этапы](Docs/15_Yard_Materials_Batch1_RU.md).
'''
p.write_text(s,encoding='utf-8')
p=ROOT/'Docs/07_Module_Catalog_RU.md';s=p.read_text(encoding='utf-8')
for i,name in enumerate(names):
    s=s.replace(f'../Source/Yard/v002/Modules/{name}/{name}.blend',f'../Source/Yard/v003/Modules/{name}/{name}.blend')
    s=s.replace(f'../Renders/Yard/v002/{name}.png',f'../Renders/Checkpoint_14/v019/{name}.png')
    tris=reports[i+2]['checks'][0]['triangles']
    lines=s.splitlines()
    for j,line in enumerate(lines):
        if line.startswith('|') and f'[{name}]' in line:
            fields=line.split('|');fields[3]=f' {tris:,} ';lines[j]='|'.join(fields)
    s='\n'.join(lines)+'\n'
p.write_text(s,encoding='utf-8')
p=ROOT/'Docs/03_Progress_RU.md';s=p.read_text(encoding='utf-8');marker='## v019 — материалы дровника и дров'
if marker not in s:s+='\n'+marker+'''\n
- Два предмета получили материалы и UV0; кора переиспользована из Oak_Kit.
- У черепицы дровника восстановлена толщина, юбки конька посажены на кровлю.
- Сборка: Assembly/v019, полная галерея: Yard/v003, два отдельных модуля: Yard/v003/Modules.
- Дом остаётся v018; его геометрия и материалы сохранены.
- Проверены четыре сохранённых файла, UV, геометрия и встроенные изображения.
- Остальные 15 дворовых модулей и настенный фонарь пока без финальных материалов.
'''
p.write_text(s,encoding='utf-8')
(ROOT/'Docs/CONTINUE_HERE_RU.md').write_text('''# Точка продолжения — сборка v019

Завершён небольшой этап материалов дровника и штабеля дров.

- Общая сцена: Source/Assembly/v019/Cottage_Courtyard.blend.
- Дом отдельно: Source/Roof/v018/House_Cottage_A.blend (без новых изменений).
- Галерея всех 17 дворовых модулей: Source/Yard/v003/Cottage_Yard_Kit.blend.
- Два обновлённых модуля: Source/Yard/v003/Modules/SM_Woodshed_A и SM_LogStack_A.
- Другие 15 дворовых модулей пока в Source/Yard/v002/Modules.
- Описание: Docs/15_Yard_Materials_Batch1_RU.md.
- Проверки: QA/yard_materials_v019_readback.json.
- Изображения: Renders/Checkpoint_14/v019.

Следующий небольшой этап — колодец и ведро: дерево, камень, черепица,
верёвка и металл. Использовать готовые материалы дома и этого этапа,
но проверить UV, толщину старых черепиц и посадку конька колодца.
Далее по партиям: мебель/ящики/забор, бочки/тачка/пень, растения/горшки/декор.
Настенный фонарь дома также ещё серый. Растительность окружения, земля,
LOD/коллизии/lightmap и экспорт впереди. Сохранять новые версии;
в CURRENT.json учитывать yard_module_overrides, не запускать старые издатели документации.
''',encoding='utf-8')
print('YARD_DOCUMENTATION_COMPLETE')
