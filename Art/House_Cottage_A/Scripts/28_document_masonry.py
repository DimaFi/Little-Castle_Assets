"""Advance CURRENT only after both v017 saved files pass validation."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
reports=json.loads((ROOT/'QA/masonry_v017_readback.json').read_text(encoding='utf-8'))
assert len(reports)==2 and {r['mode'] for r in reports}=={'house','assembly'}
assert all(r['geometry_and_pivots_unchanged'] and r['uv_within_safe_crops'] and not r['issues']
           and r['packed_masonry_images']==6 and r['ridge_max_gap_m']<=.004 for r in reports)
for rel in ['House_Hero.png','Courtyard_Hero.png','Foundation_Detail.png','Chimney_Detail.png']:
    assert (ROOT/'Renders/Checkpoint_12/v017'/rel).exists()
p=ROOT/'CURRENT.json';data=json.loads(p.read_text(encoding='utf-8'))
data.update(house='Source/Roof/v017/House_Cottage_A.blend',assembly='Source/Assembly/v017/Cottage_Courtyard.blend',
            masonry_notes='Docs/13_Masonry_Materials_RU.md',
            stage='house masonry, plaster, roof, timber and openings textured; lantern and yard materials next; engine export pending')
p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
p=ROOT/'README.md';s=p.read_text(encoding='utf-8')
s=s.replace('**Актуальная версия v016: исправлена посадка конька и добавлена штукатурка.',
            '**Актуальная версия v017: добавлены материалы каменного основания, ступеней и дымохода.')
s=s.replace('Source/Roof/v016/House_Cottage_A.blend','Source/Roof/v017/House_Cottage_A.blend')
s=s.replace('Source/Assembly/v016/Cottage_Courtyard.blend','Source/Assembly/v017/Cottage_Courtyard.blend')
s=s.replace('Камень вне дверной арки, фонарь и двор пока серые; экспорт ещё не готов.',
            'Основание, ступени и дымоход получили материалы в v017. Фонарь и двор пока серые; экспорт ещё не готов.')
s=s.replace('Renders/Checkpoint_11/v016/Courtyard_Hero.png','Renders/Checkpoint_12/v017/Courtyard_Hero.png')
s=s.replace('`Source/Roof/v016`: актуальный дом, посадка конька и штукатурка.',
            '`Source/Roof/v016`: сохранённый этап конька и штукатурки.\n- `Source/Roof/v017`: актуальный дом с материалами кладки.')
s=s.replace('`Source/Assembly/v016`: актуальная совместная сцена.',
            '`Source/Assembly/v016`: предыдущая совместная сцена.\n- `Source/Assembly/v017`: актуальная совместная сцена.')
s=s.replace('Штукатурка выполнена в v016. Далее — каменное основание и дымоход.',
            'Штукатурка выполнена в v016, камень — в v017. Далее — фонарь, затем материалы дворовых модулей.')
marker='## Материалы кладки v017'
if marker not in s:s+='\n'+marker+'\n\n80 камней основания, три ступени и 100 блоков дымохода получили UV0 и материалы.\nИспользованы внутренние участки камней из существующих карт; исходные карты\nвстроены в .blend. Геометрия и посадка конька сохранены.\n[Инструкция и ограничения](Docs/13_Masonry_Materials_RU.md).\n'
p.write_text(s,encoding='utf-8')
p=ROOT/'Docs/03_Progress_RU.md';s=p.read_text(encoding='utf-8');marker='## v017 — каменное основание и дымоход'
if marker not in s:s+='\n'+marker+'\n\n- Подготовлены UV0 и два материала для 183 деталей кладки и ступеней.\n- Повторно использованы шесть исходных карт из Mat/T_FieldStone и Mat/T_ChimneyStone.\n- Примыкание трубы использует существующий материал кровельного металла.\n- Геометрия, масштабы, pivots и исправленный конёк сохранены.\n- Проверены пробные крупные планы и повторное открытие дома/двора v017.\n- Следующий небольшой этап: материал настенного фонаря, затем дровник и дрова.\n'
p.write_text(s,encoding='utf-8')
(ROOT/'Docs/CONTINUE_HERE_RU.md').write_text('''# Точка продолжения — v017

Завершены материалы каменного основания, ступеней и дымохода.

- Дом: Source/Roof/v017/House_Cottage_A.blend.
- Дом с двором: Source/Assembly/v017/Cottage_Courtyard.blend.
- Инструкция: Docs/13_Masonry_Materials_RU.md.
- Проверки: QA/masonry_v017_readback.json.
- Рендеры: Renders/Checkpoint_12/v017.

Следующий небольшой этап — настенный фонарь дома: металл, стекло и мягкий
тёплый свет. Сначала проверить устройство mesh и разделение материалов,
не перекрыть фонарём дверь и не изменить силуэт. Затем отдельным этапом
материалы дровника и штабеля дров с переносом в сборку и самостоятельные модули.

Каменные карты в Mat изображают кладку целиком: для отдельных камней уже
выбраны безопасные участки без швов, координаты есть в Scripts/27_masonry_materials.py.
Их можно переиспользовать на колодце/ограде после проверки UV масштаба.

Сохранить все прежние версии. Новую сборку начинать с v017, не запускать
старые генераторы документации поверх CURRENT.json. Двор пока серый;
растительность, земля/дорожки, LOD, коллизии, lightmap и экспорт ещё впереди.
''',encoding='utf-8')
print('MASONRY_DOCUMENTATION_COMPLETE')
