"""Проверка проекта статьи перед подачей: python checks/check_paper.py. Код 0 — можно подавать.

Проверяется форма: структура проекта, ссылки, обезличивание, обязательные разделы и пометки.
Содержание статьи и верность чисел проверяют верификатор проекта и автор.
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
problems, passed, warnings = [], [], []


def check(ok: bool, text: str) -> None:
    (passed if ok else problems).append(text)


def read(rel: str) -> str:
    f = ROOT / rel
    return f.read_text(encoding="utf-8", errors="replace") if f.is_file() else ""


# 1. структура
for rel in ("AGENTS.md", "STATUS.md", "diary.md", "ONTOLOGY.yaml", "GLOSSARY.md", "WRITING.md",
            "research/problem.md", "lit/lit.md", "paper/paper.tex"):
    check((ROOT / rel).is_file(), f"есть {rel}")
for rel in ("AGENTS.md", "research/problem.md", "lit/lit.md", "GLOSSARY.md"):
    check("<" not in re.sub(r"`[^`]*`", "", read(rel)) or not re.search(r"<[А-Яа-яЁё][^>]*>", read(rel)),
          f"{rel}: заполнители в угловых скобках заменены своим текстом")
results = [f for f in (ROOT / "experiment" / "results").rglob("*") if f.is_file()] if (ROOT / "experiment" / "results").is_dir() else []
check(bool(results), "в experiment/results/ есть файл результатов")
check(len(re.findall(r"^## \d{4}-\d{2}-\d{2}", read("diary.md"), flags=re.M)) >= 3, "в diary.md не меньше трёх записей с датой")

# 2. статья: разделы, пометки, версия
paper = re.sub(r"(?<!\\)%.*", "", read("paper/paper.tex"))
check(not re.search(r"\\documentclass\[[^\]]*final[^\]]*\]", paper), "статья собирается без опции final (обезличенная версия)")
check(bool(re.search(r"\\section\*?\{(Ограничения|Limitations)", paper)), "в статье есть раздел «Ограничения»")
check(bool(re.search(r"\\section\*?\{(Проверка|Verification)", paper)), "в статье есть раздел «Проверка»")
check(bool(re.search(r"\\(porozhdeno|napisano|istochnik|generated|written|sourced)\b", paper)), "в статье есть пометки авторства")
check("\\begin{aiusage}" in paper, "в статье есть раздел об использовании ИИ-ассистентов")

# 3. ссылки
lit = read("lit/lit.md")
cited = {k.strip() for group in re.findall(r"\\cite\{([^}]*)\}", paper) for k in group.split(",")}
items = re.findall(r"\\bibitem\{([^}]*)\}\s*(?:\\textit\{)?\s*(?:de |van |von )?([A-Za-zА-Яа-яЁё\-]+)", paper)
keys = {k for k, _ in items}
check(cited <= keys, "у каждой ссылки \\cite есть запись в списке литературы" + (f": нет {sorted(cited - keys)}" if cited - keys else ""))
missing = [name for _, name in items if name not in lit]
check(not missing, "каждая работа из списка литературы записана в lit/lit.md" + (f": нет {missing}" if missing else ""))
rows = [l for l in lit.splitlines() if l.startswith("|") and re.search(r"\| *\d+ *\|", l)]
check(all(re.search(r"W\d{6,}|10\.\d{4,}/", l) for l in rows) and bool(rows), "у каждой записи lit/lit.md есть идентификатор OpenAlex или DOI")

# 4. PDF
pdf = ROOT / "paper" / "paper.pdf"
check(pdf.is_file(), "есть paper/paper.pdf")
if pdf.is_file():
    info = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout
    author = re.search(r"^Author:[ \t]*(.*)$", info, flags=re.M)
    check(not author or not author.group(1).strip(), "поле автора в метаданных PDF пустое")
    pages = re.search(r"^Pages:\s*(\d+)", info, flags=re.M)
    if pages and int(pages.group(1)) > 6:
        warnings.append(f"в PDF {pages.group(1)} страниц: основной текст — не больше четырёх")
    text = subprocess.run(["pdftotext", "-l", "1", str(pdf), "-"], capture_output=True, text=True).stdout
    check("Анонимные авторы" in text or "Anonymous authors" in text, "на первой странице стоит «Анонимные авторы»")

# 5. язык: обороты, которых в тексте быть не должно (предупреждение)
BAD = r"\bимплемент\w+|\bвалидир\w+|\bв терминах\b|важно отметить|стоит отметить|играет (ключевую|важную) роль|\bдавайте\b"
found = sorted({m.group(0).lower() for m in re.finditer(BAD, paper, flags=re.I)})
if found:
    warnings.append("в статье есть обороты из WRITING.md: " + ", ".join(found))

for t in passed:
    print("  да  ", t)
for t in problems:
    print("  НЕТ ", t)
for t in warnings:
    print("  !   ", t)
print(f"\nпройдено {len(passed)} из {len(passed) + len(problems)}")
sys.exit(1 if problems else 0)
