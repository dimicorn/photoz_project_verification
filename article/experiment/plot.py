#!/usr/bin/env python3
"""z_phot vs z_spec scatter для B, C, D — 3 панели, 20000 точек, seed=0."""
import csv
import random
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SAMPLES = ["B", "C", "D"]
N = 20000
SEED = 0

def load_predictions(sample):
    path = ROOT / "results" / f"predictions_{sample}.csv"
    z_spec, z_phot = [], []
    with open(path) as f:
        reader = csv.DictReader(f)
        for r in reader:
            z_spec.append(float(r["z_spec"]))
            z_phot.append(float(r["z_phot"]))
    return np.array(z_spec), np.array(z_phot)

fig, axes = plt.subplots(1, 3, figsize=(15, 4.5), sharey=True)

for i, s in enumerate(SAMPLES):
    z_spec, z_phot = load_predictions(s)
    rng = random.Random(SEED)
    idx = rng.sample(range(len(z_spec)), min(N, len(z_spec)))
    zs = z_spec[idx]
    zp = z_phot[idx]

    ax = axes[i]
    # scatter с alpha
    ax.scatter(zs, zp, s=4, alpha=0.3, color="#1f77b4", edgecolors="none")

    # линия y=x
    lims = (0, max(zs.max(), zp.max()) * 1.05)
    ax.plot(lims, lims, "k--", lw=0.8, alpha=0.5, label="y = x")

    # полосы ±0.15(1+z)
    z_vals = np.linspace(0, lims[1], 200)
    ax.fill_between(z_vals,
                    z_vals - 0.15 * (1 + z_vals),
                    z_vals + 0.15 * (1 + z_vals),
                    alpha=0.15, color="orange", label="±0.15(1+z)")

    ax.set_xlim(0, lims[1])
    ax.set_ylim(0, lims[1])
    ax.set_xlabel(r"$z_{\mathrm{spec}}$")
    ax.set_title(f"Sample {s}")
    if i == 0:
        ax.set_ylabel(r"$z_{\mathrm{phot}}$")

# Легенда только на последней панели
axes[2].legend(loc="upper left", fontsize=8)

fig.supxlabel(r"$z_{\mathrm{spec}}$", fontsize=12)
fig.supylabel(r"$z_{\mathrm{phot}}$", fontsize=12)
fig.tight_layout()

out = ROOT / "article" / "paper" / "figures" / "zphot_zspec.pdf"
out.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(str(out), dpi=150)
plt.close(fig)
print(f"Saved {out}")