# [Sol 6 High][P1] Проверить portable checkout и зависимости арт-релизов

Исполнитель: **Sol 6 / High** (`gpt-6-sol`, `reasoning_effort=high`). Это параметры для ручного запуска, Issue сам агента не запускает.

Репозиторий: `DimaFi/Little-Castle_Assets`. База: актуальный **`main`**, включая published LFS payload; исторические коммиты не переписывать. Сначала прочитать `AGENTS.md`, `README.md`, `docs/GITHUB_HANDOFF_2026-10-08.md` и game handoff в `DimaFi/Little-Castle`.

Общие ограничения: конечная карта, детерминизм/negative chunk seams, plain authoritative data отдельно от presentation, Built-in renderer, без watermills/URP/HDRP/зеркального выравнивания ресурсов. Не редактировать чужие файлы без согласованной переуступки. Перед изменениями проверить актуальные commits и работающих исполнителей. При отсутствии Unity/Blender/LFS не объявлять проверки PASS: зафиксировать точную команду и необходимость проверки на ПК.

## Результат
Свежий LFS checkout новых Source/Releases должен быть пригоден для чтения/проверки без старых E:/CozySettlement и Downloads paths. Не объявлять всю историческую библиотеку перенесённой: legacy Art/Mat binaries остаются local-only.

## Владение файлами
`Tools/sync_asset_book.py`, `Tools/package_bridge_v002.py`, `Tools/verify_git_publication.py`; новые `Tools/verify_portable_releases.py`, `Tools/test_portable_releases.py`;
`docs/GITHUB_HANDOFF_2026-10-08.md`, новый `docs/PORTABLE_RELEASE_AUDIT.md`;
`Source/Architecture/Bridge_Stone_A/v002/{build_bridge,validate_bridge}.py` только для path/dependency fixes, без изменения модели/математики;
при необходимости `.gitattributes`, `.gitignore` для точных LFS rules.
Публичные контракты: CLI diagnostics/catalog validation only. Immutable `Releases/**`, `bridge_contract.py`, модели, material assets и оба каталога не редактировать; новая версия нужна для art changes.

## Зависимости
Независимый audit, можно параллельно с game baseline/routing. Prefab integration должна дождаться положительной проверки конкретного Bridge v002 пакета.

## Приёмка
- [ ] LFS pointers vs payload различаются, missing objects дают ясную ошибку.
- [ ] Все release manifest SHA-256, packed/source texture dependencies, dimensions и script imports проверены.
- [ ] Git checkout не меняет raw bytes release text (CRLF/LF).
- [ ] Portable paths для новых bridge recipes; никаких бинарных placeholder substitutions.
- [ ] 23 new records и legacy catalog не смешаны без отдельной migration; IDs сохранены.
- [ ] Python tests могут идти в cloud; Blender rebuild/visual checks только с реальным Blender и полными input assets.
- [ ] Отчёт с точными пакетами, missing dependencies, командами, коммитом и pending PC checks.
