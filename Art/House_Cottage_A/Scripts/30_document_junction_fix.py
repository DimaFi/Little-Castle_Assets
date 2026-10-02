"""Publish v018 after saved-file and timber-module validation."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
reports=json.loads((ROOT/'QA/junctions_v018_readback.json').read_text(encoding='utf-8'))
assert len(reports)==2 and all(r['other_geometry_unchanged'] and not r['stats']['issues'] and r['ridge_max_gap_m']<=.004 for r in reports)
module=json.loads((ROOT/'QA/timber_v002_readback.json').read_text(encoding='utf-8'))
assert module['matches_house_v018'] and module['native_scene_saved']
p=ROOT/'CURRENT.json';data=json.loads(p.read_text(encoding='utf-8'))
data.update(house='Source/Roof/v018/House_Cottage_A.blend',assembly='Source/Assembly/v018/Cottage_Courtyard.blend',
            timber_module='Source/Modules/Timber_v002/SM_Cottage_TimberFrame_A.blend',
            junction_notes='Docs/14_Post_Dormer_Junctions_RU.md',
            stage='corner posts exposed and dormer tile junction fitted; lantern and yard materials next; engine export pending')
p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
p=ROOT/'README.md';s=p.read_text(encoding='utf-8')
s=s.replace('**Актуальная версия v017: добавлены материалы каменного основания, ступеней и дымохода.',
            '**Актуальная версия v018: исправлены видимость угловых стоек и примыкание черепицы к люкарне.')
for a,b in [('Source/Roof/v017/House_Cottage_A.blend','Source/Roof/v018/House_Cottage_A.blend'),
            ('Source/Assembly/v017/Cottage_Courtyard.blend','Source/Assembly/v018/Cottage_Courtyard.blend'),
            ('Source/Modules/Timber_v001/SM_Cottage_TimberFrame_A.blend','Source/Modules/Timber_v002/SM_Cottage_TimberFrame_A.blend'),
            ('Renders/Checkpoint_12/v017/Courtyard_Hero.png','Renders/Checkpoint_13/v018/Courtyard_Hero.png')]:s=s.replace(a,b)
s=s.replace('`Source/Roof/v017`: актуальный дом с материалами кладки.',
            '`Source/Roof/v017`: сохранённый этап материалов кладки.\n- `Source/Roof/v018`: актуальный дом, исправлены стойки и примыкания люкарны.')
s=s.replace('`Source/Assembly/v017`: актуальная совместная сцена.',
            '`Source/Assembly/v017`: предыдущая совместная сцена.\n- `Source/Assembly/v018`: актуальная совместная сцена.')
marker='## Исправление стоек и люкарны v018'
if marker not in s:s+='\n'+marker+'\n\nУгловые стойки вынесены из плоскости штукатурки. Локальная черепица подогнана\nк люкарне, чрезмерно открытые металлические примыкания скрыты под кровлей.\nОбновлён отдельный каркас Timber_v002. [Подробности](Docs/14_Post_Dormer_Junctions_RU.md).\n'
p.write_text(s,encoding='utf-8')
p=ROOT/'Docs/03_Progress_RU.md';s=p.read_text(encoding='utf-8');marker='## v018 — исправления по отмеченным участкам'
if marker not in s:s+='\n'+marker+'\n\n- Четыре угловые стойки вынесены на 90 мм наружу по X.\n- Пересобрана местная черепица вокруг люкарны, уменьшен чрезмерный вырез.\n- Тёмные участки оказались металлическими примыканиями, а не отсутствующей штукатуркой.\n- Повторно открыты дом и сборка, проверены UV/геометрия, сохранена посадка конька.\n- Отдельный каркас обновлён в Timber_v002. Старые версии сохранены.\n'
p.write_text(s,encoding='utf-8')
(ROOT/'Docs/CONTINUE_HERE_RU.md').write_text('''# Точка продолжения — v018

По замечаниям пользователя исправлены угловые стойки и избыточный вырез
черепицы вокруг люкарны. Материалы v017 сохранены.

- Дом: Source/Roof/v018/House_Cottage_A.blend.
- Дом с двором: Source/Assembly/v018/Cottage_Courtyard.blend.
- Отдельный каркас: Source/Modules/Timber_v002/SM_Cottage_TimberFrame_A.blend.
- Описание: Docs/14_Post_Dormer_Junctions_RU.md.
- Проверки: QA/junctions_v018_readback.json, QA/timber_v002_readback.json.
- Крупные планы: Renders/Checkpoint_13/v018.

Следующий небольшой этап остаётся прежним: настенный фонарь (металл, стекло,
мягкий тёплый свет), затем материалы дровника и дров отдельной итерацией.
Работать от v018, сохранять новые версии и переносить изменения в сборку.
Двор пока серый; растительность, земля, LOD/коллизии/lightmap и экспорт впереди.
Старые генераторы документации не запускать поверх текущего CURRENT.json.
''',encoding='utf-8')
folder=ROOT/'Source/Modules/Timber_v002'
(folder/'README_RU.md').write_text('''# SM_Cottage_TimberFrame_A — v002

Самостоятельная сцена Blender 4.4.3 с материалами, студией и камерой.
25 элементов каркаса соответствуют дому v018; четыре угловые стойки вынесены
на 90 мм наружу по X для видимости на боковых стенах. Метры, Z вверх.
Numpad 0 — общий вид. Модель в коллекции SM_Cottage_TimberFrame_A_v002,
студию не экспортировать. Каркас сохраняет координаты сборки дома.
Карты встроены, UV0 не предназначены для lightmap; игровой экспорт не готов.
Предыдущий Timber_v001 сохранён как историческая версия.
''',encoding='utf-8')
# The catalogue's current module link should agree with CURRENT.
p=ROOT/'Docs/07_Module_Catalog_RU.md';s=p.read_text(encoding='utf-8')
s=s.replace('Timber_v001/SM_Cottage_TimberFrame_A.blend','Timber_v002/SM_Cottage_TimberFrame_A.blend')
p.write_text(s,encoding='utf-8')
print('JUNCTION_DOCUMENTATION_COMPLETE')
