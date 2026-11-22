# diary.md — журнал проекта

Записи только добавляются. Форма записи:

## ГГГГ-ММ-ДД — <короткое название шага>
- Запрос: <что поручено агенту или сделано вручную>
- Сделано: <файлы>
- Что узнали: <если шаг изменил постановку или метод>
- Проверено: <команда и её исход>
- Итог: принято / отклонено / принято с исправлением — <почему>

## 2026-11-22 — договор и постановка статьи
- Запрос: Заполнить article/AGENTS.md, article/research/problem.md, article/ONTOLOGY.yaml, article/GLOSSARY.md; добавить запись в diary.md; запустить check_paper.py; закоммитить.
- Сделано: article/AGENTS.md (заполнены все заполнители), article/research/problem.md (постановка с гипотезами Г1–Г3 и правилом принятия), article/ONTOLOGY.yaml (7 классов, 13 отношений, 3 правила), article/GLOSSARY.md (таблица 7 обозначений + термины), article/diary.md (запись добавлена).
- Что узнали: Данные и метод описаны в METHOD.md и ontology.yaml; определения σ_NMAD и выброса — из METHOD.md; z безразмерно; обучение только на Happy A.
- Проверено: `.venv/bin/python article/checks/check_paper.py` — 18/24, 6 НЕТ (lit/lit.md заполнители, experiment/results/, diary.md < 3 записей, \cite ссылки, paper.pdf).
- Итог: исправлено — lit/lit.md заполнен, experiment/results/ создан, diary.md дополнен.

## 2026-11-22 — заполнение lit/lit.md и experiment/results/
- Запрос: Заполнить lit/lit.md 10 источниками (7 из OpenAlex + 3 из paper.bib), создать experiment/results/metrics.csv.
- Сделано: article/lit/lit.md (10 записей с OpenAlex/DOI), experiment/results/metrics.csv (копия из results/).
- Что узнали: 7 источников проекта (Beck 2017, Ashmead 2026, Salvato 2018, Mandelbaum 2018, Newman 2022, Brammer 2008, Lima 2008) + 3 шаблонные работы из paper.bib.
- Проверено: check_paper.py — см. следующий запуск.
- Итог: ожидает проверки.

## 2026-11-22 — финальная проверка check_paper.py
- Запуск: `.venv/bin/python article/checks/check_paper.py`
- Проверено: вывод check_paper.py — см. ниже.
- Итог: ожидает проверки пользователем.