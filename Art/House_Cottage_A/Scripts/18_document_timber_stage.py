"""Update current pointers only after successful timber and verge read-back reports."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
wood=json.loads((ROOT/'QA/timber_v010_readback.json').read_text(encoding='utf-8'))
cuts=json.loads((ROOT/'QA/timber_v011_readback.json').read_text(encoding='utf-8'))
assert len(wood)==3 and all(not x['issues'] and x['uv_degenerate_faces']==0 for x in wood)
assert len(cuts)==2 and all(x['closed_cuts'] and x['other_geometry_unchanged'] for x in cuts)
for path in ['Source/Materials/v011/House_Cottage_A.blend','Source/Assembly/v011/Cottage_Courtyard.blend',
             'Source/Modules/Timber_v001/SM_Cottage_TimberFrame_A.blend']:
    assert (ROOT/path).exists(),path
p=ROOT/'CURRENT.json';current=json.loads(p.read_text(encoding='utf-8'))
current.update(assembly='Source/Assembly/v011/Cottage_Courtyard.blend',house='Source/Materials/v011/House_Cottage_A.blend',
    timber_module='Source/Modules/Timber_v001/SM_Cottage_TimberFrame_A.blend',standalone_module_count=22,
    materials_notes='Docs/09_Timber_Materials_RU.md',
    stage='openings and structural timber UV/materials; border tile cuts fixed; remaining roof thickness audit next')
p.write_text(json.dumps(current,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

p=ROOT/'README.md';s=p.read_text(encoding='utf-8')
s=s.replace('Source/Materials/v009/House_Cottage_A.blend','Source/Materials/v011/House_Cottage_A.blend')
s=s.replace('Source/Assembly/v009/Cottage_Courtyard.blend','Source/Assembly/v011/Cottage_Courtyard.blend')
s=s.replace('Текущий этап — первые материалы двери и окон. Для них выполнены направленные\nUV0 и подключены существующие карты древесины; исправлена посадка оконных вставок.\nОстальная часть дома и двор пока серые. Экспорт в движок ещё не готов.\nОписание: [Дверь и окна — материалы](Docs/08_Openings_Materials_RU.md).',
'''Текущий этап — материалы двери, окон и деревянного каркаса. Для них выполнены
направленные UV0, существующие карты древесины упакованы в .blend. Исправлены
посадка оконных вставок и пересечения крайних черепиц с торцевыми досками.
Стены, камень вне дверной арки, черепица и двор пока серые; экспорт ещё не готов.
Описание: [Деревянный каркас и края крыши](Docs/09_Timber_Materials_RU.md).''')
s=s.replace('`Renders/Checkpoint_06/v009/Courtyard_Hero.png`','`Renders/Checkpoint_07/v011/Courtyard_Hero.png`')
row='| Каркас отдельным модулем | `Source/Modules/Timber_v001/SM_Cottage_TimberFrame_A.blend` |'
if row not in s:s=s.replace('| Галерея 17 модулей |',row+'\n| Галерея 17 модулей |')
s=s.replace('- `Source/Materials/v009`: актуальный дом, первый этап материалов двери/окон.',
'''- `Source/Materials/v009`: сохранённый первый этап материалов двери/окон.
- `Source/Materials/v010`: материал каркаса до подрезки крайних черепиц.
- `Source/Materials/v011`: актуальный дом.
- `Source/Modules/Timber_v001`: самостоятельный каркас с материалами.''')
s=s.replace('- `Source/Assembly/v009`: актуальная совместная сцена с материалами двери/окон.',
'''- `Source/Assembly/v009` и `v010`: сохранённые предыдущие сборки.
- `Source/Assembly/v011`: актуальная совместная сцена.''')
s=s.replace('Следующий этап — основной деревянный каркас.','Деревянный каркас выполнен на следующем этапе v011.')
marker='## Этап каркаса v011'
if marker not in s:s+='\n'+marker+'''\n
25 деревянных деталей с UV0 и материалами; отдельный каркас добавлен в каталог
(всего 22 самостоятельных модуля). Подрезаны 44 крайних черепицы, восстановлена
необходимая толщина их срезов. Отчёты: `QA/timber_v010_readback.json` и
`QA/timber_v011_readback.json`.

Следующий приоритет — проверка толщины остальной черепицы и конька до материалов
крыши. В старых исходниках обнаружены открытые поверхности; их замкнутость
не проверялась ранними тестами площади треугольников. Дальше — штукатурка и камень.
'''
p.write_text(s,encoding='utf-8')

p=ROOT/'Docs/07_Module_Catalog_RU.md';s=p.read_text(encoding='utf-8')
s=s.replace('21 файл: 17 дворовых модулей и 4 варианта двери/окон.','22 файла: 17 дворовых модулей, 4 варианта двери/окон и деревянный каркас.')
row='| Деревянный каркас дома | [SM_Cottage_TimberFrame_A](../Source/Modules/Timber_v001/SM_Cottage_TimberFrame_A.blend) | 11,996 | [Каркас — превью](../Renders/Checkpoint_07/v010/Timber_Frame_Module.png) |'
if row not in s:s=s.replace('\nТреугольники измерены', '\n'+row+'\n\nТреугольники измерены')
# The row must remain inside the Markdown table, without a separating blank line.
s=s.replace('\n\n'+row,'\n'+row)
p.write_text(s,encoding='utf-8')

(ROOT/'Source/Modules/Timber_v001/README_RU.md').write_text('''# SM_Cottage_TimberFrame_A

25 деталей каркаса и деревянных кромок крыши, 11 996 треугольников с модификаторами.
Каркас совместим с домом v011. Метры, Z вверх, фасад −Y; исходные координаты дома.
File → Append → SM_Cottage_TimberFrame_A.blend → Collection → SM_Cottage_TimberFrame_A.
В собранном доме уже есть этот каркас: повторно поверх него не добавлять.

Материал M_Cottage_StructuralTimber_A, UV0 вдоль деталей, около 539 px/м.
Три исходные карты T_Timber встроены в .blend. UV повторяемая, с перекрытиями;
lightmap, LOD и игровой экспорт не подготовлены. Студия/свет/камера — только для просмотра.
Numpad 0 — сохранённая камера. Подробности: Docs/09_Timber_Materials_RU.md.
''',encoding='utf-8')
p=ROOT/'Docs/03_Progress_RU.md';s=p.read_text(encoding='utf-8');marker='## v011 — деревянный каркас и края крыши'
if marker not in s:s+='\n'+marker+'''\n
- 25 деревянных деталей: направленная UV0, материал из существующего T_Timber.
- Отдельный модуль Timber_v001, актуальные дом/сборка v011.
- Исправлены 44 крайних черепицы, устранены выступы через торцевые доски.
- Геометрия остальных деталей и пивоты сохранены; новые файлы повторно открыты.
- Проверены общий, крупный и задний ракурсы, каркас отдельно, UV-сетка.
- Требуется проверить толщину остальной крыши: у старых крайних прототипов
  обнаружены открытые поверхности. Это следующий приоритет до текстур крыши.
'''
p.write_text(s,encoding='utf-8')
print('TIMBER_CURRENT_UPDATED',current['house'])
