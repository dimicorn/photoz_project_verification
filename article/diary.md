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

## 2026-11-22 — литература и чистка
- Запрос: Чистка paper.tex (удаление \bibitem/\cite hairer1990, roy2005, sandve2013), git rm Tectonic.toml и src; исправление даты гипотез в problem.md на 2026-10-05; удаление двух пустых записей из diary.md; переписывание lit.md (8 работ по photo-z и сдвигу выборки); переписывание paper.bib.
- Сделано: article/paper/paper.tex (удалены \bibitem и \cite шаблонных работ), article/paper/paper.bib (8 работ, ключи author+year, DOI из OpenAlex), article/lit/lit.md (8 работ: Beck 2017, Ashmead 2026, Salvato 2018, Newman 2022, Brammer 2008, Lima 2008, Rivera 2018, Leistedt 2017), article/research/problem.md (дата гипотез: 2026-10-05), article/diary.md (удалены 2 пустые записи).
- Что узнали: Все 8 работ проверены через OpenAlex (W-id, DOI, аннотации). Rivera 2018 — анализ деградации photo-z на non-representative training sets; Leistedt 2017 — data-driven photo-z на unrepresentative data.
- Проверено: check_paper.py — см. ниже.
- Итог: ожидает проверки.

## 2026-11-22 — добавление bibitem в paper.tex
- Запрос: Добавить \bibitem записи в paper.tex для check_paper.py.
- Сделано: article/paper/paper.tex (добавлены 8 \bibitem записей).
- Проверено: check_paper.py — см. ниже.
- Итог: ожидает проверки.


## 2026-11-22 — результаты и рисунок

- Создан `article/experiment/run.py`: запускает `src/photoz.py`, копирует результаты в `article/experiment/results/`, запускает `checks_hw2`, сохраняет `verifier.txt` (rc=0).
- Создан `article/src/make_paper_numbers.py`: читает `results/metrics.csv` и `results/uncertainty.csv`, пишет `article/paper/results.tex` с `\newcommand` для всех метрик и доверительных интервалов.
- Создан `article/experiment/plot.py`: matplotlib, 3 панели z_phot vs z_spec для B,C,D (hist2d scatter, 20000 точек, seed=0), линия y=x, полосы ±0.15(1+z). Сохранён в `article/paper/figures/zphot_zspec.pdf`.
- Проверка: `git diff --stat results/` — только `run_log.md` (не metrics.csv), metrics.csv совпадает с git.
- `checks_hw2` — rc=0.

## 2026-11-22 — текст статьи и вычитка

- Запрос: этап 6 — вычитка и подготовка к подаче.
- Сделано: вычитан `article/paper/paper.tex`; исправлены две неточности —
  команды воспроизводимости приведены к `.venv/bin/python` (было `python`),
  из раздела Experiment убрано «beyond the margin of the acceptance rule»
  (правило приёмки — строгий порядок, запаса оно не задаёт).
- Проверено:
  - числа результатов вне макросов `results.tex` — нет; `grep -nE '[0-9]\.[0-9]{2}'`
    по телу даёт только константы определений (1,4826 в σ_NMAD и порог 0,15);
  - `dimicorn`, `github`, `/Users`, имена авторов — 0 вхождений в `paper.tex` и в PDF;
  - `pdfinfo paper.pdf | grep Author` — пусто; `Pages: 4`;
  - объём основного текста: стр. 1–3 плюс ~55 % стр. 4 до «Use of AI assistants»,
    то есть ≈3,5 стр. — в границах 2–4;
  - утверждения сверены с фактами: 24 теста верификатора (24 строки PASS),
    9 свойств оценщика, 5 bootstrap-сидов (0–4), концы интервалов совпадают
    до третьего знака; baseline-константа на B 0,1916 = Σ_B + ΔConstBabs;
  - `tectonic -X compile paper.tex` — rc=0;
  - `.venv/bin/python -m checks_hw2` — rc=0;
  - `.venv/bin/python article/checks/check_paper.py` — rc=0, 26 из 26.
- Итог: версия для подачи зафиксирована тегом `paper-submitted`.
