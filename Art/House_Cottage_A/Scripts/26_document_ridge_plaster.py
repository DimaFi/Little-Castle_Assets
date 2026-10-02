"""Publish v016 only after successful saved-file validation."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
reports=json.loads((ROOT/'QA/ridge_plaster_v016_readback.json').read_text(encoding='utf-8'))
assert len(reports)==2
assert all(r['other_geometry_unchanged'] and r['max_contact_gap_m']<=.004 and not r['caps']['issues']
           and not r['plaster']['issues'] and r['packed_plaster_images']==3 for r in reports)
p=ROOT/'CURRENT.json';d=json.loads(p.read_text(encoding='utf-8'))
d.update(house='Source/Roof/v016/House_Cottage_A.blend',assembly='Source/Assembly/v016/Cottage_Courtyard.blend',
    plaster_notes='Docs/12_Ridge_Seating_Plaster_RU.md',ridge_notes='Docs/12_Ridge_Seating_Plaster_RU.md',
    stage='ridge seating corrected; plaster, roof, timber and openings textured; masonry next; engine export pending')
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
p=ROOT/'README.md';s=p.read_text(encoding='utf-8')
s=s.replace('**Пауза после пробного рендера штукатурки. [Точка продолжения](Docs/CONTINUE_HERE_RU.md). Актуальная сохранённая сцена — v014; v015 ещё не собрана.**',
    '**Актуальная версия v016: исправлена посадка конька и добавлена штукатурка. [Следующий этап](Docs/CONTINUE_HERE_RU.md).**')
s=s.replace('Source/Roof/v014/House_Cottage_A.blend','Source/Roof/v016/House_Cottage_A.blend')
s=s.replace('Source/Assembly/v014/Cottage_Courtyard.blend','Source/Assembly/v016/Cottage_Courtyard.blend')
s=s.replace('Текущий этап — крыша, дверь, окна и деревянный каркас имеют UV и материалы.',
    'Текущий этап — крыша, стены, дверь, окна и деревянный каркас имеют UV и материалы; конёк подогнан к скатам.')
s=s.replace('Стены, камень вне дверной арки и двор пока серые; экспорт ещё не готов.',
    'Камень вне дверной арки, фонарь и двор пока серые; экспорт ещё не готов.')
s=s.replace('Renders/Checkpoint_09/v014/Courtyard_Hero.png','Renders/Checkpoint_11/v016/Courtyard_Hero.png')
s=s.replace('- `Source/Roof/v014`: актуальный дом с материалами крыши.',
    '- `Source/Roof/v014`: сохранённый этап материалов крыши.\n- `Source/Roof/v016`: актуальный дом, посадка конька и штукатурка.')
s=s.replace('- `Source/Assembly/v014`: актуальная совместная сцена.',
    '- `Source/Assembly/v014`: предыдущая сборка.\n- `Source/Assembly/v016`: актуальная совместная сцена.')
s=s.replace('Далее — штукатурка стен и люкарны, затем каменное основание и дымоход.',
    'Штукатурка выполнена в v016. Далее — каменное основание и дымоход.')
marker='## Посадка конька и штукатурка v016'
if marker not in s:s+='\n'+marker+'''\n
Исправлено примыкание 27 коньковых сегментов к кровле. В 2059 проверенных точках
нет положительного зазора. Замкнутость и UV сегментов сохранены; остальная
геометрия не изменена. Девять деталей стен и люкарны получили штукатурку из Mat.
Дом и сборка повторно открыты, карты встроены. [Подробности](Docs/12_Ridge_Seating_Plaster_RU.md).
'''
p.write_text(s,encoding='utf-8')
p=ROOT/'Docs/03_Progress_RU.md';s=p.read_text(encoding='utf-8');marker='## v016 — посадка конька и штукатурка'
if marker not in s:s+='\n'+marker+'''\n
- Работа возобновлена по просьбе пользователя после паузы на пробе штукатурки.
- По замечанию пользователя исправлены 20 основных и 7 малых коньковых сегментов.
- Выполнены замеры контакта, визуальная проверка и повторное открытие двух файлов.
- Завершены UV0 и материал девяти деталей стен/фронтонов/люкарны, карты упакованы.
- Актуальны Roof/v016 и Assembly/v016. Итоговая v015 не создавалась.
- Дальше: каменное основание и дымоход; затем остальные материалы и игровая подготовка.
'''
p.write_text(s,encoding='utf-8')
(ROOT/'Docs/CONTINUE_HERE_RU.md').write_text('''# Точка продолжения — v016

Пауза от 2026-10-01 завершена новой просьбой пользователя. Следующая сохранённая
версия — v016: исправлено примыкание конька и завершена штукатурка стен/люкарны.

- Дом: Source/Roof/v016/House_Cottage_A.blend.
- Дом с двором: Source/Assembly/v016/Cottage_Courtyard.blend.
- Инструкция этапа: Docs/12_Ridge_Seating_Plaster_RU.md.
- Проверки: QA/ridge_plaster_v016_readback.json.
- Рендеры: Renders/Checkpoint_11/v016.

Следующий небольшой этап — UV/материалы каменного основания и дымохода.
Проверить доступные Mat/T_FieldStone и Mat/T_ChimneyStone: это изображения
кладки, поэтому нельзя оборачивать всю кладку вокруг каждого отдельного камня.
Сначала выбрать подходящий способ использования карт и проверить отдельный
камень/небольшую группу, затем перенести на дом и сборку в новой версии.

Сохранить крупные формы и силуэт. Ранее сделанные материалы и все версии оставить.
Фонарь и двор ещё серые. Игровые LOD, коллизии, lightmap и экспорт не готовы.
Не запускать старые генераторы документации поверх CURRENT.json.
''',encoding='utf-8')
print('RIDGE_PLASTER_CURRENT_UPDATED',d['house'])
