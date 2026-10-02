"""Catalogues the files actually delivered, without modifying Blender sources."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
yard=json.loads((ROOT/'QA/yard_v002.json').read_text(encoding='utf-8'))
openings=json.loads((ROOT/'QA/opening_modules.json').read_text(encoding='utf-8'))
readback=json.loads((ROOT/'QA/module_readback.json').read_text(encoding='utf-8'))
assert readback['passed'] and readback['files_checked']==21
names={'SM_Woodshed_A':'Дровник','SM_LogStack_A':'Штабель дров','SM_Well_A':'Колодец','SM_Barrel_A':'Бочка','SM_Bucket_A':'Ведро','SM_WoodBench_A':'Скамейка','SM_WoodTable_A':'Стол','SM_FlowerBox_A':'Ящик с цветами','SM_Pot_A':'Горшок','SM_Crate_A':'Ящик','SM_FenceBay_A':'Секция деревянного забора','SM_Gate_A':'Калитка','SM_StoneWall_A':'Каменная ограда','SM_Stump_Axe_A':'Пень с топором','SM_Birdhouse_A':'Скворечник','SM_Signpost_A':'Указатель','SM_Wheelbarrow_A':'Тачка','SM_Door_Entrance_A':'Входная дверь с каменной аркой','SM_Window_Open_A':'Окно с открытыми ставнями','SM_Window_Small_A':'Маленькое окно','SM_Window_Closed_A':'Окно с закрытыми ставнями'}
rows=[]
for rec in readback['modules']:
    p=ROOT/rec['file'];name=rec['name'];title=names[name]
    cat='Окна и дверь' if 'Openings_' in rec['file'] else 'Двор'
    image='Renders/Openings/v002/'+name+'.png' if cat=='Окна и дверь' else 'Renders/Yard/v002/'+name+'.png'
    rows.append(f"| {title} | [{name}](../{p.relative_to(ROOT).as_posix()}) | {rec['triangles']:,} | [{cat} — превью](../{image}) |")
    text=f'''# {title} — {name}

Открыть `{p.name}` в Blender 4.4.3. Сцена и коллекция `{name}` содержат модель.
Файл самостоятельный, с камерой и светом; Numpad 0 — вид из камеры.
Для переноса в другую сцену: File → Append → этот .blend → Collection → `{name}`.
Не переносить коллекцию студии `90_STUDIO`: она содержит только свет, камеры и пол.

Единицы — метры, Z вверх, основной фронт −Y. Коллекцию удобно ставить через
Collection Instance: её локальное начало задаёт положение целого модуля.
Отдельные детали остаются редактируемыми. Внутри есть общие mesh-данные:
Make Single User → Object Data перед уникальной правкой связанной детали.

Стадия: серая геометрия. Финальные UV, материалы, LOD, collision и игровые
экспорты не готовы. Polycount с текущими модификаторами: {rec['triangles']:,}
треугольников, {rec['objects']} mesh-объектов. Это не утверждённый игровой бюджет.

Проверено повторное открытие файла, сохранение камеры, масштаб и отсутствие
вырожденных треугольников. Общий отчёт: `QA/module_readback.json` в корне комплекта.
Превью: `{image}` в корне комплекта. Исходные файлы дерева и старых props не изменены.
'''
    if name in ['SM_Gate_A','SM_Door_Entrance_A','SM_Window_Open_A','SM_Window_Closed_A']:
        text+='\nДля створок использовать пустые объекты `CTRL_*`: поворот локальной Z вокруг петли. Это ручные контроллеры, без анимационных клипов и логики движка.\n'
    if name=='SM_Birdhouse_A':text+='\nПереиспользован `Art/Props/Birdhouse_01.blend`; серая копия геометрически очищена. Модуль предназначен для крепления на стойке, а не для установки на грунт.\n'
    if name=='SM_FlowerBox_A':text+='\nЦветы и листья взяты из `Art/Vegetation/Oak_Kit/Cozy_Oak_Kit.blend`; здесь используется серая копия для проверки формы.\n'
    (p.parent/'README_RU.md').write_text(text,encoding='utf-8')

(ROOT/'Docs/07_Module_Catalog_RU.md').write_text('# Каталог самостоятельных модулей\n\n21 файл: 17 дворовых модулей и 4 варианта двери/окон. Все ссылки ведут на актуальные версии.\n\n| Модуль | Blender | Треугольники | Изображение |\n|---|---|---:|---|\n'+'\n'.join(rows)+'\n\nТреугольники измерены с модификаторами. Это исходная геометрия, не игровые LOD.\n',encoding='utf-8')

(ROOT/'README.md').write_text('''# House Cottage A — дом и модульный двор

**Общая сцена: [Source/Assembly/v008/Cottage_Courtyard.blend](Source/Assembly/v008/Cottage_Courtyard.blend).**
**Дом отдельно: [Source/Openings/v007/House_Cottage_A.blend](Source/Openings/v007/House_Cottage_A.blend).**

Текущий этап — серая геометрия. Доработаны дверь и ставни, добавлен настенный
фонарь, создан дворовый набор. Материалы и экспорт в движок ещё не готовы.
Предыдущие версии, Oak_Kit, старые Cottage и Art/Props сохранены.

## Быстрый доступ

| Что нужно | Где находится |
|---|---|
| Дом с двором | `Source/Assembly/v008/Cottage_Courtyard.blend` |
| Дом без двора | `Source/Openings/v007/House_Cottage_A.blend` |
| Галерея 17 модулей | `Source/Yard/v002/Cottage_Yard_Kit.blend` |
| Отдельные дворовые модели | `Source/Yard/v002/Modules/<имя>/<имя>.blend` |
| Входная дверь и три окна | `Source/Modules/Openings_v002/<имя>/<имя>.blend` |
| Каталог со ссылками и статистикой | [Docs/07_Module_Catalog_RU.md](Docs/07_Module_Catalog_RU.md) |
| Обзор двора на одном листе | `Renders/Yard/v002/Contact_Sheet.jpg` |
| Общая композиция, три ракурса | `Renders/Checkpoint_05/v008` |
| Дверь и окно на доме крупно | `Renders/Checkpoint_04/v007` |
| Самостоятельные дверные/оконные модули | `Renders/Openings/v002` |

## Состав

Дом: цоколь, стены с проёмами, отдельные балки, два изогнутых ската, объёмная
черепица, конёк, люкарна и её примыкания, дымоход, окна, ставни, дверь и фонарь.

Двор: дровник, штабель дров, колодец, бочка, ведро, скамейка, стол, цветочный
ящик, горшок, ящик, секция забора, калитка, каменная ограда, пень с топором,
скворечник, указатель и тачка. Фонарь, скворечник и цветы переиспользуют
существующие наработки. Дополнительно сохранены входная дверь, большое открытое
окно, большое закрытое окно и маленькое окно как четыре самостоятельных модуля.

У каждой отдельной модели есть собственный README_RU.md рядом с .blend.

## Как редактировать

Blender 4.4.3, метры, Z вверх, фронт −Y. Numpad 0 — сохранённая камера.
Дом остаётся в `COL_House_Cottage_A`, дворовые размещения — в
`COL_Courtyard_Placement`. Сцена `Yard_Module_Sources` содержит исходные
коллекции дворовых модулей; для удобного отдельного редактирования лучше
открывать файлы из `Source/Yard/v002/Modules`.

Двор размещён экземплярами коллекций. Выберите `PLACE_*`, чтобы передвинуть
целый модуль. Object → Apply → Make Instances Real создаст редактируемые
объекты конкретного экземпляра; не делать этого массово без необходимости.
Изменения mesh общих деталей отражаются на связанных экземплярах. Для
уникального варианта использовать Make Single User → Object Data.

Дверь, ставни и калитка имеют контроллеры `CTRL_*` у петель. Поворот локальной
Z меняет положение створки. Это геометрическая подготовка, не готовая игровая
анимация. Стекло пока серое, двор показан на студийном полу без terrain.

File → Append → файл модуля → Collection → коллекция с именем ассета переносит
модуль. Студию `90_STUDIO`, камеры и свет в игру не экспортировать.

## Структура и версии

- `References`: исходные изображения и текстовое описание.
- `Source/Blockout`: история v001–v004.
- `Source/Refinement/v005`: исправленные примыкания и фундамент.
- `Source/Roof/v006`: первая черепица.
- `Source/Openings/v007`: актуальный дом отдельно, дверь/ставни/фонарь.
- `Source/Yard/v002`: актуальный дворовый набор; v001 — ранняя итерация.
- `Source/Modules/Openings_v002`: актуальная дверь и окна; v001 — ранняя упаковка.
- `Source/Assembly/v008`: актуальная совместная сцена.
- `Scripts`, `Docs`, `QA`, `Renders`: генераторы, инструкции, проверки, изображения.
- `Exports`: резерв, новых игровых FBX пока нет.

## Проверено

Осмотрены общий вид дома, дверь/окно крупно, все 17 модулей, самостоятельные
варианты окон/двери и три ракурса двора. 21 самостоятельный .blend повторно
открыт: проверены геометрия, единицы и наличие камеры. В сборке проверены
10 контроллеров: дверь, восемь ставней и калитка. Отчёты:
`QA/module_readback.json`, `yard_v002.json`, `opening_modules.json`,
`openings_v007.json`, `courtyard_v008.json`.

Эти проверки не доказывают точное совпадение с концептом, отсутствие всех
пересечений или готовность для движка. Двор — пример размещения, ограда
намеренно представлена отдельными секциями; навигация не тестировалась.

## Продолжение

1. Художественная проверка крупных форм и подрезки крыши, доработка слабых узлов.
2. Направленные UV древесины, черепицы и кладки; единая texel density.
3. Подключение пригодных материалов из Mat по аудиту `Docs/02_Materials_Audit_RU.md`.
4. Растительность на стенах, почва и тропинки, дополнительные вариации props.
5. Снижение количества объектов, оптимизация, LOD и collision, экспорт и тест в движке.

Курица с дополнительного листа не создавалась: персонаж/риг — отдельная задача.
Дерево уже есть в Oak_Kit, оно не включено в серую композицию дома.

Генераторы не читают ручные правки текущих сцен. Сохраняйте ручную работу через
Save As. Каждый скрипт проверяет существование своего итогового .blend и не
перезаписывает его. Запускать только отдельным фоновым Blender-процессом, не
внутри несохранённой рабочей сцены. Последовательность и команды:
[Docs/06_Openings_Yard_RU.md](Docs/06_Openings_Yard_RU.md).
''',encoding='utf-8')

(ROOT/'CURRENT.json').write_text(json.dumps({'assembly':'Source/Assembly/v008/Cottage_Courtyard.blend','house':'Source/Openings/v007/House_Cottage_A.blend','yard_kit':'Source/Yard/v002/Cottage_Yard_Kit.blend','yard_modules':'Source/Yard/v002/Modules','opening_modules':'Source/Modules/Openings_v002','catalogue':'Docs/07_Module_Catalog_RU.md','stage':'grey geometry; UV, materials, optimization and engine export pending','standalone_module_count':21},indent=2),encoding='utf-8')
print('DOCUMENTED',len(rows),'standalone modules')
