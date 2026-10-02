"""Publish v009 pointers only after Blender read-back validation succeeds."""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
checks = json.loads((ROOT/'QA/materials_v009_validate.json').read_text(encoding='utf-8'))
assert len(checks) == 6 and all(r['non_glass_geometry_and_all_pivots_unchanged'] for r in checks)
assert all(not r['issues'] and r['uv_degenerate_faces'] == 0 for r in checks)

current = json.loads((ROOT/'CURRENT.json').read_text(encoding='utf-8'))
current.update({
    'assembly': 'Source/Assembly/v009/Cottage_Courtyard.blend',
    'house': 'Source/Materials/v009/House_Cottage_A.blend',
    'opening_modules': 'Source/Modules/Openings_Materials_v002',
    'stage': 'door/window UV0 and first materials complete; rest grey; optimization and engine export pending',
    'materials_notes': 'Docs/08_Openings_Materials_RU.md',
    'grey_house': 'Source/Openings/v007/House_Cottage_A.blend',
    'grey_assembly': 'Source/Assembly/v008/Cottage_Courtyard.blend',
})
(ROOT/'CURRENT.json').write_text(json.dumps(current,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

p=ROOT/'README.md'; text=p.read_text(encoding='utf-8')
text=text.replace('Source/Assembly/v008/Cottage_Courtyard.blend', 'Source/Assembly/v009/Cottage_Courtyard.blend')
text=text.replace('Source/Openings/v007/House_Cottage_A.blend','Source/Materials/v009/House_Cottage_A.blend')
text=text.replace('Source/Modules/Openings_v002','Source/Modules/Openings_Materials_v002')
text=text.replace('| Общая композиция, три ракурса | `Renders/Checkpoint_05/v008` |',
                  '| Актуальный общий вид двора | `Renders/Checkpoint_06/v009/Courtyard_Hero.png` |')
text=text.replace('| Дверь и окно на доме крупно | `Renders/Checkpoint_04/v007` |',
                  '| Дверь и окно на доме крупно | `Renders/Checkpoint_06/v009/House_Door.png`, `House_Window.png` |')
text=text.replace('| Самостоятельные дверные/оконные модули | `Renders/Openings/v002` |',
                  '| Самостоятельные дверные/оконные модули | `Renders/Checkpoint_06/v009/Openings_Contact_Sheet.jpg` |')
text=text.replace('Текущий этап — серая геометрия. Доработаны дверь и ставни, добавлен настенный\nфонарь, создан дворовый набор. Материалы и экспорт в движок ещё не готовы.',
'''Текущий этап — первые материалы двери и окон. Для них выполнены направленные
UV0 и подключены существующие карты древесины; исправлена посадка оконных вставок.
Остальная часть дома и двор пока серые. Экспорт в движок ещё не готов.
Описание: [Дверь и окна — материалы](Docs/08_Openings_Materials_RU.md).''')
text=text.replace('Стекло пока серое, двор показан на студийном полу без terrain.',
                  'Оконные вставки пока непрозрачные, двор показан на студийном полу без terrain.')
text=text.replace('- `Source/Openings/v007`: актуальный дом отдельно, дверь/ставни/фонарь.',
'''- `Source/Openings/v007`: сохранённый серый дом.
- `Source/Materials/v009`: актуальный дом, первый этап материалов двери/окон.''')
text=text.replace('- `Source/Modules/Openings_Materials_v002`: актуальная дверь и окна; v001 — ранняя упаковка.',
'''- `Source/Modules/Openings_Materials_v002`: актуальная дверь и окна с материалами.
- `Source/Modules/Openings_v002`: сохранённые серые модули.
- `Source/Modules/Openings_Materials_v001`: промежуточная проба материалов.''')
text=text.replace('- `Source/Assembly/v009`: актуальная совместная сцена.',
'''- `Source/Assembly/v009`: актуальная совместная сцена с материалами двери/окон.
- `Source/Assembly/v008`: сохранённая серая совместная сцена.''')
marker='## Проверка этапа материалов v009'
if marker not in text:
    text += '\n'+marker+'\n\nПовторно открыты 4 модуля, дом и общая сцена. Геометрия без вырожденных\nтреугольников, UV0 без нулевых площадей. Геометрия кроме намеренно исправленных\nоконных вставок и все исходные трансформации сохранены. Карты модулей упакованы.\nОтчёт: `QA/materials_v009_validate.json`. Следующий этап — основной деревянный каркас.\n'
p.write_text(text,encoding='utf-8')

p=ROOT/'Docs/07_Module_Catalog_RU.md';text=p.read_text(encoding='utf-8')
text=text.replace('../Source/Modules/Openings_v002','../Source/Modules/Openings_Materials_v002')
text=text.replace('../Renders/Openings/v002','../Renders/Checkpoint_06/v009')
note='\nДверь и три оконных модуля имеют первый проход материалов и UV0. Двор пока серый.\nПодробнее: [этап материалов v009](08_Openings_Materials_RU.md).\n'
if note not in text:text+=note
p.write_text(text,encoding='utf-8')

records=json.loads((ROOT/'QA/materials_v009_modules.json').read_text(encoding='utf-8'))
for r in records:
    folder=ROOT/r['file'];assert folder.exists()
    (folder.parent/'README_RU.md').write_text(f'''# {r['name']}

Актуальный модуль с UV0 и материалами: {folder.name}.
Blender 4.4.3; метры; Z вверх; фронт −Y. Камера сохранена: Numpad 0.
Треугольники с модификаторами: {r['triangles']:,}. Это исходник, не игровой LOD.

File → Append → этот файл → Collection → {r['name']}.
Студию, свет и камеры переносить только для просмотра.
Контроллеры CTRL_* вращаются вокруг локальной Z у петель; исходная поза сохранена.

Карты древесины встроены в .blend; оригиналы находятся в CozySettlement/Mat.
UV0 содержит повторно используемые участки текстур, не предназначен для lightmap.
Стекло — непрозрачная отражающая вставка без интерьера.
Документация: Art/House_Cottage_A/Docs/08_Openings_Materials_RU.md.
Проверки: QA/materials_v009_validate.json. Старый серый вариант: Source/Modules/Openings_v002.
''',encoding='utf-8')

p=ROOT/'Docs/03_Progress_RU.md';text=p.read_text(encoding='utf-8')
marker='## v009 — UV и материалы двери/окон'
if marker not in text:
    text+='\n'+marker+'''\n
- Направленные UV0 для дверных досок, ставней, рам и изогнутых арок.
- Повторно использованы карты DoorWood, Shutters, T_Timber, упакованы в .blend.
- Параметрические железо, известняк и непрозрачная оконная вставка.
- Устранён зазор оконной вставки за рамой.
- Дом Materials/v009, сборка Assembly/v009, отдельные модули Openings_Materials_v002.
- Проверены рендеры, сетка UV, повторное открытие 6 файлов и сохранность геометрии/пивотов.
- Следом: основной деревянный каркас; затем штукатурка/камень и отдельно крыша.
'''
p.write_text(text,encoding='utf-8')

rend=ROOT/'Renders/Checkpoint_06/v009'
sheet=Image.new('RGB',(1100,1160),'#25282b');draw=ImageDraw.Draw(sheet)
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',22)
names=[('SM_Door_Entrance_A','Входная дверь'),('SM_Window_Open_A','Открытое окно'),
       ('SM_Window_Small_A','Маленькое окно'),('SM_Window_Closed_A','Закрытое окно')]
for i,(name,label) in enumerate(names):
    x=(i%2)*550;y=(i//2)*580
    im=Image.open(rend/(name+'.png')).convert('RGB').resize((530,530),Image.Resampling.LANCZOS)
    sheet.paste(im,(x+10,y+10));draw.text((x+18,y+548),label,font=font,fill='white')
sheet.save(rend/'Openings_Contact_Sheet.jpg',quality=94)
print('MATERIAL_DOCUMENTATION_CURRENT',len(records))
