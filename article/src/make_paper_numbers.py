#!/usr/bin/env python3
"""Читает metrics.csv и uncertainty.csv, пишет article/paper/results.tex."""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
METRICS = ROOT / "results" / "metrics.csv"
UNCERT = ROOT / "results" / "uncertainty.csv"
OUT = ROOT / "article" / "paper" / "results.tex"

# --- metrics.csv ---
rows = {}
with open(METRICS) as f:
    for r in csv.DictReader(f):
        rows[r["sample"]] = r

B = rows["B"]
C = rows["C"]
D = rows["D"]

# --- uncertainty.csv (galaxy_bootstrap, sigma_nmad / outlier_frac) ---
# Берём seed=0 для low/high
unc = {}
with open(UNCERT) as f:
    for r in csv.DictReader(f):
        if r["variant"] != "galaxy_bootstrap":
            continue
        key = (r["sample"], r["metric"])
        if r["seed"] == "0":
            unc[key] = (float(r["low"]), float(r["high"]))

# Форматирование
def fmt4(v):
    return f"{float(v):.4f}"

def fmt1pct(v):
    return f"{float(v)*100:.1f}"

def fmt_n(n):
    s = str(int(n))
    # разделитель тысяч: {,}
    parts = []
    while len(s) > 3:
        parts.insert(0, s[-3:])
        s = s[:-3]
    parts.insert(0, s)
    return "{,}".join(parts)

lines = []
lines.append(r"\newcommand{\Kneigh}{10}")
lines.append("")

# B
lines.append(r"\newcommand{\NB}{" + fmt_n(B["n"]) + r"}")
lines.append(r"\newcommand{\BiasB}{" + fmt4(B["bias"]) + r"}")
lines.append(r"\newcommand{\SigmaB}{" + fmt4(B["sigma_nmad"]) + r"}")
lines.append(r"\newcommand{\OutB}{" + fmt1pct(B["outlier_frac"]) + r"}")
lines.append("")

# C
lines.append(r"\newcommand{\NC}{" + fmt_n(C["n"]) + r"}")
lines.append(r"\newcommand{\BiasC}{" + fmt4(C["bias"]) + r"}")
lines.append(r"\newcommand{\SigmaC}{" + fmt4(C["sigma_nmad"]) + r"}")
lines.append(r"\newcommand{\OutC}{" + fmt1pct(C["outlier_frac"]) + r"}")
lines.append("")

# D
lines.append(r"\newcommand{\ND}{" + fmt_n(D["n"]) + r"}")
lines.append(r"\newcommand{\BiasD}{" + fmt4(D["bias"]) + r"}")
lines.append(r"\newcommand{\SigmaD}{" + fmt4(D["sigma_nmad"]) + r"}")
lines.append(r"\newcommand{\OutD}{" + fmt1pct(D["outlier_frac"]) + r"}")
lines.append("")

# Uncertainty: sigma_nmad low/high
for sample, label in [("B", "B"), ("C", "C"), ("D", "D")]:
    lo, hi = unc[(sample, "sigma_nmad")]
    lines.append(rf"\newcommand{{\Sigma{label}lo}}{{{fmt4(lo)}}}")
    lines.append(rf"\newcommand{{\Sigma{label}hi}}{{{fmt4(hi)}}}")

lines.append("")

# Uncertainty: outlier_frac low/high
for sample, label in [("B", "B"), ("C", "C"), ("D", "D")]:
    lo, hi = unc[(sample, "outlier_frac")]
    lines.append(rf"\newcommand{{\Out{label}lo}}{{{fmt1pct(lo)}}}")
    lines.append(rf"\newcommand{{\Out{label}hi}}{{{fmt1pct(hi)}}}")

lines.append("")

# --- Разности sigma_nmad с 95%-интервалами ---
# hypothesis_delta: C-B, D-B, D-C (независимый бутстреп);
# paired_k10_vs_k1 и paired_k10_vs_const: парный бутстреп на B.
delta = {}
with open(UNCERT) as f:
    for r in csv.DictReader(f):
        if r["metric"] != "delta_sigma_nmad" or r["seed"] != "0":
            continue
        delta[(r["variant"], r["sample"])] = (
            float(r["estimate"]), float(r["low"]), float(r["high"]))

DELTAS = [
    (("hypothesis_delta", "C-B"), "DeltaCB"),
    (("hypothesis_delta", "D-B"), "DeltaDB"),
    (("hypothesis_delta", "D-C"), "DeltaDC"),
    (("paired_k10_vs_k1", "B"), "DeltaKoneB"),
    (("paired_k10_vs_const", "B"), "DeltaConstB"),
]

for key, name in DELTAS:
    est, lo, hi = delta[key]
    lines.append(rf"\newcommand{{\{name}}}{{{fmt4(est)}}}")
    lines.append(rf"\newcommand{{\{name}lo}}{{{fmt4(lo)}}}")
    lines.append(rf"\newcommand{{\{name}hi}}{{{fmt4(hi)}}}")

# Модули разностей с базовыми линиями: в тексте нужен размер проигрыша базовой линии
for key, name in [(("paired_k10_vs_k1", "B"), "DeltaKoneBabs"),
                  (("paired_k10_vs_const", "B"), "DeltaConstBabs")]:
    est, _, _ = delta[key]
    lines.append(rf"\newcommand{{\{name}}}{{{fmt4(abs(est))}}}")

OUT.write_text("\n".join(lines) + "\n")
print(f"Written {OUT} ({len(lines)} lines)")