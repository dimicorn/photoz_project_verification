#!/usr/bin/env python3
"""Запуск photoz, копирование результатов, проверка verifier."""
import subprocess
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
EXP_RES = ROOT / "article" / "experiment" / "results"
EXP_RES.mkdir(parents=True, exist_ok=True)

FILES = [
    "results/metrics.csv",
    "results/predictions_B.csv",
    "results/predictions_C.csv",
    "results/predictions_D.csv",
    "results/uncertainty.csv",
    "results/real_error_before.txt",
    "results/real_error_after.txt",
    "results/inject_feats.txt",
]

# 1. Запуск src/photoz.py
print("=== Запуск src/photoz.py ===")
r = subprocess.run(
    [".venv/bin/python", "src/photoz.py"],
    cwd=ROOT,
    capture_output=True,
    text=True,
    timeout=600,
)
print(r.stdout)
if r.stderr:
    print(r.stderr, file=sys.stderr)
if r.returncode != 0:
    print("ERROR: photoz.py failed", file=sys.stderr)
    sys.exit(1)

# 2. Копирование результатов
for f in FILES:
    src = ROOT / f
    dst = EXP_RES / src.name
    if src.exists():
        shutil.copy2(src, dst)
        print(f"  copied {f} -> {dst.name}")
    else:
        print(f"  SKIP {f} (not found)", file=sys.stderr)

# 3. Запуск checks_hw2
print("\n=== Запуск checks_hw2 ===")
r2 = subprocess.run(
    [".venv/bin/python", "-m", "checks_hw2"],
    cwd=ROOT,
    capture_output=True,
    text=True,
    timeout=600,
)
verifier_path = EXP_RES / "verifier.txt"
with open(verifier_path, "w") as vf:
    vf.write(f"returncode: {r2.returncode}\n")
    vf.write(r2.stdout)
    if r2.stderr:
        vf.write(r2.stderr)
print(f"  verifier saved to {verifier_path.name} (rc={r2.returncode})")

# 4. Сравнение metrics.csv с git-версией
print("\n=== Сравнение metrics.csv с git ===")
r3 = subprocess.run(
    ["git", "diff", "--stat", "results/"],
    cwd=ROOT,
    capture_output=True,
    text=True,
)
if r3.stdout.strip():
    print(f"  DIFF FOUND:\n{r3.stdout}")
else:
    print("  OK: results/metrics.csv совпадает с git-версией")

print("\nDone.")