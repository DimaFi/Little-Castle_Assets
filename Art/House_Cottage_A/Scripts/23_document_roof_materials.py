"""Publish v014 roof material stage after read-back checks."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
reports=json.loads((ROOT/'QA/roof_materials_v014_readback.json').read_text(encoding='utf-8'))
assert len(reports)==3
assert all(r['geometry_unchanged'] and r['roof_closed'] and r['packed_images']==3 for r in reports[:2])
assert not reports[2]['issues']
p=ROOT/'CURRENT.json';d=json.loads(p.read_text(encoding='utf-8'))
d.update(house='Source/Roof/v014/House_Cottage_A.blend',assembly='Source/Assembly/v014/Cottage_Courtyard.blend',
    roof_notes='Docs/11_Roof_Materials_RU.md',roof_material_study='Source/Materials/v014/Roof_Material_Study_v003.blend',
    stage='openings, timber and roof UV/materials; plaster and masonry next; engine export pending')
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
p=ROOT/'README.md';s=p.read_text(encoding='utf-8')
s=s.replace('Roof_Material_Study_v002.blend','Roof_Material_Study_v003.blend')
s=s.replace('Source/Roof/v012/House_Cottage_A.blend','Source/Roof/v014/House_Cottage_A.blend')
s=s.replace('Source/Assembly/v012/Cottage_Courtyard.blend','Source/Assembly/v014/Cottage_Courtyard.blend')
s=s.replace('Текущий этап — восстановлена толщина черепицы и конька. Дверь, окна и деревянный каркас уже имеют материалы.',
    'Текущий этап — крыша, дверь, окна и деревянный каркас имеют UV и материалы.')
s=s.replace('Стены, камень вне дверной арки, черепица и двор пока серые; экспорт ещё не готов.',
    'Стены, камень вне дверной арки и двор пока серые; экспорт ещё не готов.')
s=s.replace('Renders/Checkpoint_08/v012/Courtyard_Hero.png','Renders/Checkpoint_09/v014/Courtyard_Hero.png')
s=s.replace('- `Source/Roof/v012`: актуальный дом с исправленной толщиной крыши.',
    '- `Source/Roof/v012`: сохранённая проверенная геометрия крыши.\n- `Source/Roof/v013`: промежуточная цветовая проба.\n- `Source/Roof/v014`: актуальный дом с материалами крыши.\n- `Source/Materials/v014`: техническая сцена образцов черепицы.')
s=s.replace('- `Source/Assembly/v012`: актуальная совместная сцена.',
    '- `Source/Assembly/v012`: предыдущая сборка.\n- `Source/Assembly/v014`: актуальная совместная сцена.')
s=s.replace('Следующий этап — UV и материалы черепицы и конька.','UV и материалы крыши выполнены в v014.')
marker='## Материалы крыши v014'
if marker not in s:s+='\n'+marker+'''\n
574 элемента получили UV0 и терракоту из существующих карт RoofTile.
Карты встроены в .blend. Геометрия v012 сохранена, замкнутость повторно проверена.
Подробности: [UV и материалы крыши](Docs/11_Roof_Materials_RU.md).
Техническая сцена: `Source/Materials/v014/Roof_Material_Study_v003.blend`.
Далее — штукатурка стен и люкарны, затем каменное основание и дымоход.
'''
p.write_text(s,encoding='utf-8')
p=ROOT/'Docs/03_Progress_RU.md';s=p.read_text(encoding='utf-8');marker='## v014 — UV и материалы черепицы'
if marker not in s:s+='\n'+marker+'''\n
- UV0 и материалы 574 деталей крыши; исходные RoofTile карты встроены.
- Использована внутренняя область карты без белого фона и нарисованных кромок.
- Основания крыши и примыкания люкарны получили отдельные одноцветные материалы.
- Материалы проверены на отдельных образцах, на доме, сзади и в общей сцене.
- Проверочная сетка UV, неизменность геометрии/пивотов и повторное открытие трёх файлов.
- Актуальны Roof/v014 и Assembly/v014; v013 — промежуточная цветовая проба.
- Следом штукатурка, затем камень. Игровая оптимизация и экспорт не выполнены.
'''
p.write_text(s,encoding='utf-8')
(ROOT/'Source/Materials/v014/README_RU.md').write_text('''# Образцы материала крыши

Roof_Material_Study_v003.blend: три образца — основная черепица, черепица люкарны,
полукруглый конёк. Это техническая сцена проверки материала, не игровой комплект.
Numpad 0 — камера. Коллекция Roof_Material_Samples содержит образцы.
Сцена в метрах; все три карты RoofTile упакованы в .blend.
Актуальный собранный дом: Source/Roof/v014/House_Cottage_A.blend.
Инструкция: Docs/11_Roof_Materials_RU.md.
''',encoding='utf-8')
print('ROOF_MATERIALS_CURRENT_UPDATED',d['house'])
