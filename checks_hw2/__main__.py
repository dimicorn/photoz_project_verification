"""Запуск верификатора ДЗ 2: src/photoz.py → три скрипта → итог.

Запуск: .venv/bin/python -m checks_hw2
"""

import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = [
    "контракт",
    ROOT / "checks_hw2" / "test_data_contract.py",
    "свойства",
    ROOT / "checks_hw2" / "test_photoz_properties.py",
    "метрики",
    ROOT / "checks_hw2" / "test_metrics_consistency.py",
]


def main():
    # 0. Запускаем src/photoz.py
    print("=== Запуск src/photoz.py ===")
    result = subprocess.run(
        [sys.executable, str(ROOT / "src" / "photoz.py")],
        capture_output=True, text=True, cwd=str(ROOT),
    )
    if result.returncode != 0:
        print(f"src/photoz.py FAILED (код {result.returncode})")
        if result.returncode < 0:
            print(f"скрипт убит сигналом {-result.returncode} (вероятно, не хватило памяти)")
        print(result.stdout if result.stdout else "")
        print(result.stderr if result.stderr else "")
        sys.exit(1)
    print("src/photoz.py OK")

    # 1. Запускаем три скрипта
    all_codes = []
    script_results = []
    for i in range(0, len(SCRIPTS), 2):
        label = SCRIPTS[i]
        path = SCRIPTS[i + 1]
        print(f"\n=== {label}: {path.name} ===")
        r = subprocess.run(
            [sys.executable, str(path)],
            capture_output=True, text=True, cwd=str(ROOT),
        )
        print(r.stdout if r.stdout else "")
        if r.stderr:
            print(r.stderr if r.stderr else "")
        if r.returncode < 0:
            print(f"скрипт убит сигналом {-r.returncode} (вероятно, не хватило памяти)")
        all_codes.append(r.returncode)
        # Подсчитаем PASS/FAIL/ERROR из вывода
        stdout = r.stdout
        n_pass = stdout.count("  PASS:")
        n_fail = stdout.count("  FAIL:")
        n_error = stdout.count("  ERROR:")
        script_results.append((label, n_pass, n_fail + n_error, r.returncode))

    # 2. Итог
    codes_str = ", ".join(str(c) for c in all_codes)
    verdict = "ПРИНЯТО" if all(c == 0 for c in all_codes) else "НЕ ПРИНЯТО"
    print(f"\nконтракт: {all_codes[0]}, свойства: {all_codes[1]}, метрики: {all_codes[2]} — {verdict}")

    # 3. Запись в run_log.md
    log_path = ROOT / "results" / "run_log.md"
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    try:
        head = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, cwd=str(ROOT),
        ).stdout.strip()
    except Exception:
        head = "unknown"

    lines = [f"\n## {date} (commit {head})\n"]
    for label, np_, nf, code in script_results:
        lines.append(f"- {label}: код={code}, {np_} passed, {nf} failed\n")
    lines.append(f"- Итог: {verdict}\n")

    with open(log_path, "a", encoding="utf-8") as f:
        f.writelines(lines)

    sys.exit(0 if all(c == 0 for c in all_codes) else 1)


if __name__ == "__main__":
    main()