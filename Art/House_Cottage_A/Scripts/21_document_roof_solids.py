"""Publish v012 pointers after validated closed roof geometry."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
report=json.loads((ROOT/'QA/roof_solids_v012_readback.json').read_text(encoding='utf-8'))
assert len(report)==2
assert all(r['outer_vertices_preserved'] and r['other_geometry_unchanged'] and not r['geometry']['issues'] for r in report)
assert all(g['open_objects']==0 for r in report for g in r['groups'].values())
regression=json.loads((ROOT/'QA/roof_bake_regression.json').read_text(encoding='utf-8'))
assert regression['nonmanifold_edges']==0 and regression['remaining_modifiers']==0
p=ROOT/'CURRENT.json';data=json.loads(p.read_text(encoding='utf-8'))
data.update(house='Source/Roof/v012/House_Cottage_A.blend',assembly='Source/Assembly/v012/Cottage_Courtyard.blend',
            roof_notes='Docs/10_Roof_Solids_RU.md',
            stage='roof thickness and closure repaired; openings and timber textured; roof UV/materials next')
p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
p=ROOT/'README.md';s=p.read_text(encoding='utf-8')
s=s.replace('Source/Materials/v011/House_Cottage_A.blend','Source/Roof/v012/House_Cottage_A.blend')
s=s.replace('Source/Assembly/v011/Cottage_Courtyard.blend','Source/Assembly/v012/Cottage_Courtyard.blend')
s=s.replace('`Renders/Checkpoint_07/v011/Courtyard_Hero.png`','`Renders/Checkpoint_08/v012/Courtyard_Hero.png`')
s=s.replace('Текущий этап — материалы двери, окон и деревянного каркаса.',
            'Текущий этап — восстановлена толщина черепицы и конька. Дверь, окна и деревянный каркас уже имеют материалы.')
s=s.replace('- `Source/Materials/v011`: актуальный дом.',
            '- `Source/Materials/v011`: предыдущий дом с материалом каркаса.\n- `Source/Roof/v012`: актуальный дом с исправленной толщиной крыши.')
s=s.replace('- `Source/Assembly/v011`: актуальная совместная сцена.',
            '- `Source/Assembly/v011`: предыдущая сборка.\n- `Source/Assembly/v012`: актуальная совместная сцена.')
s=s.replace('Следующий приоритет — проверка толщины остальной черепицы и конька до материалов\nкрыши. В старых исходниках обнаружены открытые поверхности; их замкнутость\nне проверялась ранними тестами площади треугольников. Дальше — штукатурка и камень.',
            'Проверка толщины черепицы и конька выполнена в v012. Далее — UV и материалы крыши, затем штукатурка и камень.')
marker='## Крыша v012'
if marker not in s:s+='\n'+marker+'''\n
Замкнуты все 477 черепиц основных скатов, 70 черепиц люкарны и 27 сегментов
конька. Толщина восстановлена у 460 ранее открытых деталей; наружные вершины
сохранены. Исправлена причина потери модификаторов в генераторе прототипов.
Дом и общая сцена повторно открыты и проверены.
Подробности: [Толщина крыши](Docs/10_Roof_Solids_RU.md).
Следующий этап — UV и материалы черепицы и конька.
'''
p.write_text(s,encoding='utf-8')
p=ROOT/'Docs/03_Progress_RU.md';s=p.read_text(encoding='utf-8');marker='## v012 — толщина черепицы и конька'
if marker not in s:s+='\n'+marker+'''\n
- Проверены 574 керамические детали и 15 остальных элементов крыши.
- Толщина восстановлена у 433 черепиц и 27 сегментов конька; 70 черепиц люкарны
  и 44 ранее исправленных крайних элемента сохранены.
- Исправлен bake скрытых прототипов в генераторе 07; регрессионный тест пройден.
- Наружные вершины, положения объектов и остальная геометрия сохранены.
- Итоговые дом Roof/v012 и сборка Assembly/v012 повторно открыты и проверены.
- Следом: UV и материалы крыши, затем штукатурка и камень.
'''
p.write_text(s,encoding='utf-8')
print('ROOF_SOLIDS_CURRENT_UPDATED',data['house'])
