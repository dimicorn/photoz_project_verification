"""Эксперимент на неопределённость — пункт г) Пересмотр 1 METHOD.md."""

import argparse
import csv
import sys
from pathlib import Path

import numpy as np

# src/photoz.py доступен через sys.path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.photoz import predict_knn, load, load_ids, metrics  # noqa: E402

RES = ROOT / "results"
RES.mkdir(exist_ok=True)

SAMPLES = ["B", "C", "D"]
N_BOOT = 1000
BOOT_CHUNK = 100  # куски по 100 повторов для экономии памяти
SEEDS = [0, 1, 2, 3, 4]


def bootstrap_galaxies(train, test_ids, test_data, n_boot, seed):
    """Бутстреп по галактикам: случайный подвыбор test_data с возвращением."""
    rng = np.random.default_rng(seed)
    n = len(test_data)
    z_phot_all = predict_knn(train, test_data, k=10)
    zs_all = test_data[:, 6]
    dz_all = (z_phot_all - zs_all) / (1 + zs_all)
    bias_all = float(np.median(dz_all))
    sigma_all = float(1.4826 * np.median(np.abs(dz_all - bias_all)))
    outlier_all = float(np.mean(np.abs(dz_all) > 0.15))

    estimates = {"bias": [], "sigma_nmad": [], "outlier_frac": []}
    for chunk_start in range(0, n_boot, BOOT_CHUNK):
        chunk_size = min(BOOT_CHUNK, n_boot - chunk_start)
        indices = rng.integers(0, n, size=(chunk_size, n))
        for i in range(chunk_size):
            idx = indices[i]
            z_phot_boot = z_phot_all[idx]
            zs_boot = zs_all[idx]
            dz_boot = (z_phot_boot - zs_boot) / (1 + zs_boot)
            b = float(np.median(dz_boot))
            s = float(1.4826 * np.median(np.abs(dz_boot - b)))
            o = float(np.mean(np.abs(dz_boot) > 0.15))
            estimates["bias"].append(b)
            estimates["sigma_nmad"].append(s)
            estimates["outlier_frac"].append(o)

    intervals = {}
    for m in ["bias", "sigma_nmad", "outlier_frac"]:
        arr = np.array(estimates[m])
        intervals[m] = {
            "estimate": float(np.median(arr)),
            "low": float(np.percentile(arr, 2.5)),
            "high": float(np.percentile(arr, 97.5)),
        }
    return intervals


def subsample_A(train, test_data, seed):
    """Подвыборка 80% строк train (seed), метрики на полном test_data."""
    rng = np.random.default_rng(seed)
    n = len(train)
    n_sub = int(0.8 * n)
    idx = rng.choice(n, size=n_sub, replace=False)
    train_sub = train[idx]
    z_phot = predict_knn(train_sub, test_data, k=10)
    zs = test_data[:, 6]
    return metrics(z_phot, zs)


def baseline_constant(train, test_data):
    """Константа = медиана z_spec по train."""
    z_med = float(np.median(train[:, 6]))
    zs = test_data[:, 6]
    return metrics(np.full(len(zs), z_med), zs)


def baseline_k1(train, test_data, seed, n_boot):
    """kNN с k=1, бутстреп по test_data."""
    rng = np.random.default_rng(seed)
    n = len(test_data)
    z_phot_full = predict_knn(train, test_data, k=1)
    zs_full = test_data[:, 6]
    dz_full = (z_phot_full - zs_full) / (1 + zs_full)
    bias_full = float(np.median(dz_full))
    sigma_full = float(1.4826 * np.median(np.abs(dz_full - bias_full)))

    estimates = []
    for chunk_start in range(0, n_boot, BOOT_CHUNK):
        chunk_size = min(BOOT_CHUNK, n_boot - chunk_start)
        indices = rng.integers(0, n, size=(chunk_size, n))
        for i in range(chunk_size):
            idx = indices[i]
            dz_b = dz_full[idx]
            b = float(np.median(dz_b))
            s = float(1.4826 * np.median(np.abs(dz_b - b)))
            estimates.append((b, s))

    sigma_arr = np.array([e[1] for e in estimates])
    bias_arr = np.array([e[0] for e in estimates])
    return {
        "sigma_nmad": float(np.median(sigma_arr)),
        "sigma_low": float(np.percentile(sigma_arr, 2.5)),
        "sigma_high": float(np.percentile(sigma_arr, 97.5)),
        "bias": float(np.median(bias_arr)),
        "bias_low": float(np.percentile(bias_arr, 2.5)),
        "bias_high": float(np.percentile(bias_arr, 97.5)),
        "sigma_full": sigma_full,
        "bias_full": bias_full,
    }


def sigma_nmad(dz):
    return float(1.4826 * np.median(np.abs(dz - np.median(dz))))


def bootstrap_p(deltas):
    """Двусторонний бутстреп-p: 2·min(доля Δ≤0, доля Δ≥0)."""
    return min(1.0, 2.0 * min(float(np.mean(deltas <= 0)), float(np.mean(deltas >= 0))))


def paired_bootstrap(z_a, z_b, zs, seed, n_boot):
    """Парный бутстреп Δσ_NMAD = σ(a) − σ(b) на одних и тех же индексах галактик."""
    rng = np.random.default_rng(seed)
    n = len(zs)
    dz_a = (z_a - zs) / (1 + zs)
    dz_b = (z_b - zs) / (1 + zs)

    diffs = []
    for chunk_start in range(0, n_boot, BOOT_CHUNK):
        chunk_size = min(BOOT_CHUNK, n_boot - chunk_start)
        indices = rng.integers(0, n, size=(chunk_size, n))
        for i in range(chunk_size):
            idx = indices[i]
            diffs.append(sigma_nmad(dz_a[idx]) - sigma_nmad(dz_b[idx]))

    diffs = np.array(diffs)
    return {
        "delta_median": float(np.median(diffs)),
        "delta_low": float(np.percentile(diffs, 2.5)),
        "delta_high": float(np.percentile(diffs, 97.5)),
        "p": bootstrap_p(diffs),
    }


def holm_correction(p_values):
    """Поправка Холма (step-down): p_(i) · (m − i), с монотонностью, не больше 1."""
    p_values = np.asarray(p_values, dtype=float)
    m = len(p_values)
    order = np.argsort(p_values, kind="stable")
    p_adj = np.empty(m)
    running = 0.0
    for rank, j in enumerate(order):
        running = max(running, min(1.0, p_values[j] * (m - rank)))
        p_adj[j] = running
    return p_adj


def fmt_p(p, floor):
    """p = 0 при конечном числе повторов печатается как «< floor»."""
    return f"< {floor:g}" if p == 0 else f"{p:.4f}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-boot", type=int, default=N_BOOT)
    args = parser.parse_args()
    n_boot = args.n_boot

    print(f"Эксперимент на неопределённость, n_boot={n_boot}")

    # Загрузка данных
    train = load("A")
    test = {}
    for name in SAMPLES:
        test[name] = load(name)

    # ===== 1. Бутстреп по галактикам =====
    print("\n[1] Бутстреп по галактикам...")
    csv_rows = []
    galaxy_intervals = {}
    for name in SAMPLES:
        print(f"  {name}...", end=" ", flush=True)
        intervals = bootstrap_galaxies(train, None, test[name], n_boot, seed=0)
        galaxy_intervals[name] = intervals
        for seed in SEEDS:
            if seed == 0:
                continue
            intervals_s = bootstrap_galaxies(train, None, test[name], n_boot, seed=seed)
            for m in ["bias", "sigma_nmad", "outlier_frac"]:
                csv_rows.append({
                    "variant": "galaxy_bootstrap",
                    "sample": name,
                    "metric": m,
                    "seed": seed,
                    "estimate": intervals_s[m]["estimate"],
                    "low": intervals_s[m]["low"],
                    "high": intervals_s[m]["high"],
                })
        print(f"σ_NMAD [{intervals['sigma_nmad']['low']:.6f}, {intervals['sigma_nmad']['high']:.6f}]")

    # Проверка устойчивости концов интервала σ_NMAD между seed 0–4
    print("\n[1b] Проверка устойчивости σ_NMAD между seeds 0–4...")
    stability_ok = True
    for name in SAMPLES:
        ends = []
        for seed in SEEDS:
            iv = bootstrap_galaxies(train, None, test[name], n_boot, seed=seed)
            ends.append((iv["sigma_nmad"]["low"], iv["sigma_nmad"]["high"]))
        low_diff = max(e[0] for e in ends) - min(e[0] for e in ends)
        high_diff = max(e[1] for e in ends) - min(e[1] for e in ends)
        ok = low_diff <= 0.001 and high_diff <= 0.001
        if not ok:
            stability_ok = False
            print(f"  {name}: расхождение > 0.001 (low={low_diff:.6f}, high={high_diff:.6f})")
        else:
            print(f"  {name}: OK (low_diff={low_diff:.6f}, high_diff={high_diff:.6f})")
        for seed in SEEDS:
            iv = bootstrap_galaxies(train, None, test[name], n_boot, seed=seed)
            for m in ["bias", "sigma_nmad", "outlier_frac"]:
                csv_rows.append({
                    "variant": "galaxy_bootstrap",
                    "sample": name,
                    "metric": m,
                    "seed": seed,
                    "estimate": iv[m]["estimate"],
                    "low": iv[m]["low"],
                    "high": iv[m]["high"],
                })

    if not stability_ok:
        print("  → Расхождение > 0.001, увеличиваем n_boot до 5000...")
        n_boot = 5000
        for name in SAMPLES:
            for seed in SEEDS:
                iv = bootstrap_galaxies(train, None, test[name], n_boot, seed=seed)
                for m in ["bias", "sigma_nmad", "outlier_frac"]:
                    csv_rows.append({
                        "variant": "galaxy_bootstrap",
                        "sample": name,
                        "metric": m,
                        "seed": seed,
                        "estimate": iv[m]["estimate"],
                        "low": iv[m]["low"],
                        "high": iv[m]["high"],
                    })

    # ===== 2. 5 подвыборок по 80% A =====
    print("\n[2] 5 подвыборок по 80% A...")
    subsample_results = {name: [] for name in SAMPLES}
    for seed in SEEDS:
        for name in SAMPLES:
            m = subsample_A(train, test[name], seed)
            subsample_results[name].append(m)
            csv_rows.append({
                "variant": "subsample_80pct",
                "sample": name,
                "metric": "sigma_nmad",
                "seed": seed,
                "estimate": m["sigma_nmad"],
                "low": "",
                "high": "",
            })
            csv_rows.append({
                "variant": "subsample_80pct",
                "sample": name,
                "metric": "bias",
                "seed": seed,
                "estimate": m["bias"],
                "low": "",
                "high": "",
            })
    subsample_summary = {}
    for name in SAMPLES:
        arr_s = np.array([m["sigma_nmad"] for m in subsample_results[name]])
        arr_b = np.array([m["bias"] for m in subsample_results[name]])
        subsample_summary[name] = {
            "sigma_mean": float(np.mean(arr_s)),
            "sigma_std": float(np.std(arr_s)),
            "bias_mean": float(np.mean(arr_b)),
            "bias_std": float(np.std(arr_b)),
        }
        print(f"  {name}: σ_NMAD={subsample_summary[name]['sigma_mean']:.6f}±{subsample_summary[name]['sigma_std']:.6f}")

    # ===== 3. Базовые линии на B =====
    print("\n[3] Базовые линии на B...")
    const_b = baseline_constant(train, test["B"])
    print(f"  Константа (медиана z_spec A): σ_NMAD={const_b['sigma_nmad']:.6f}")
    csv_rows.append({
        "variant": "baseline_constant",
        "sample": "B",
        "metric": "sigma_nmad",
        "seed": 0,
        "estimate": const_b["sigma_nmad"],
        "low": "",
        "high": "",
    })

    k1_b = baseline_k1(train, test["B"], seed=0, n_boot=n_boot)
    print(f"  kNN k=1: σ_NMAD={k1_b['sigma_nmad']:.6f} [{k1_b['sigma_low']:.6f}, {k1_b['sigma_high']:.6f}]")
    csv_rows.append({
        "variant": "baseline_k1",
        "sample": "B",
        "metric": "sigma_nmad",
        "seed": 0,
        "estimate": k1_b["sigma_nmad"],
        "low": k1_b["sigma_low"],
        "high": k1_b["sigma_high"],
    })

    # Парные сравнения k=10 с базовыми линиями (одни и те же индексы галактик B, seed 0)
    zs_B = test["B"][:, 6]
    z10_B = predict_knn(train, test["B"], k=10)
    z1_B = predict_knn(train, test["B"], k=1)
    zconst_B = np.full(len(zs_B), float(np.median(train[:, 6])))
    comparisons = []
    for label, variant, z_other in [
        ("k=10 − константа (B)", "paired_k10_vs_const", zconst_B),
        ("k=10 − k=1 (B)", "paired_k10_vs_k1", z1_B),
    ]:
        pr = paired_bootstrap(z10_B, z_other, zs_B, seed=0, n_boot=n_boot)
        print(f"  Δσ_NMAD ({label}): {pr['delta_median']:.6f} [{pr['delta_low']:.6f}, {pr['delta_high']:.6f}]")
        comparisons.append({
            "pair": label,
            "kind": "парный",
            "delta": pr["delta_median"],
            "low": pr["delta_low"],
            "high": pr["delta_high"],
            "p": pr["p"],
        })
        csv_rows.append({
            "variant": variant,
            "sample": "B",
            "metric": "delta_sigma_nmad",
            "seed": 0,
            "estimate": pr["delta_median"],
            "low": pr["delta_low"],
            "high": pr["delta_high"],
        })

    # ===== 4. Гипотеза: Δσ_NMAD C−B, D−B, D−C =====
    print("\n[4] Гипотеза: Δσ_NMAD (независимый бутстреп)...")
    # Для независимого бутстреп берём dz на полных выборках
    z_phot_B = predict_knn(train, test["B"], k=10)
    z_phot_C = predict_knn(train, test["C"], k=10)
    z_phot_D = predict_knn(train, test["D"], k=10)
    dz_B = (z_phot_B - test["B"][:, 6]) / (1 + test["B"][:, 6])
    dz_C = (z_phot_C - test["C"][:, 6]) / (1 + test["C"][:, 6])
    dz_D = (z_phot_D - test["D"][:, 6]) / (1 + test["D"][:, 6])

    pairs = [("C", "B", dz_C, dz_B), ("D", "B", dz_D, dz_B), ("D", "C", dz_D, dz_C)]
    for name1, name2, dz1, dz2 in pairs:
        rng = np.random.default_rng(0)
        n1, n2 = len(dz1), len(dz2)
        deltas = []
        for chunk_start in range(0, n_boot, BOOT_CHUNK):
            chunk_size = min(BOOT_CHUNK, n_boot - chunk_start)
            idx1 = rng.integers(0, n1, size=(chunk_size, n1))
            idx2 = rng.integers(0, n2, size=(chunk_size, n2))
            for i in range(chunk_size):
                s1 = float(1.4826 * np.median(np.abs(dz1[idx1[i]] - np.median(dz1[idx1[i]]))))
                s2 = float(1.4826 * np.median(np.abs(dz2[idx2[i]] - np.median(dz2[idx2[i]]))))
                deltas.append(s1 - s2)
        deltas = np.array(deltas)
        delta_median = float(np.median(deltas))
        delta_low = float(np.percentile(deltas, 2.5))
        delta_high = float(np.percentile(deltas, 97.5))
        p_val = bootstrap_p(deltas)

        comparisons.append({
            "pair": f"{name1}−{name2}",
            "kind": "независимый",
            "delta": delta_median,
            "low": delta_low,
            "high": delta_high,
            "p": p_val,
        })
        print(f"  {name1}−{name2}: Δ={delta_median:.6f} [{delta_low:.6f}, {delta_high:.6f}], p={fmt_p(p_val, 1 / n_boot)}")
        csv_rows.append({
            "variant": "hypothesis_delta",
            "sample": f"{name1}-{name2}",
            "metric": "delta_sigma_nmad",
            "seed": 0,
            "estimate": delta_median,
            "low": delta_low,
            "high": delta_high,
        })

    # Поправка Холма на все 5 сравнений (2 с базовыми линиями + 3 гипотезы), METHOD «Пересмотр 1 г»
    p_vals = np.array([c["p"] for c in comparisons])
    p_holm = holm_correction(p_vals)
    for c, ph in zip(comparisons, p_holm):
        c["p_holm"] = ph
        # практический порог: весь 95%-интервал Δ дальше 0.005 от нуля
        practical = c["low"] > 0.005 or c["high"] < -0.005
        significant = ph < 0.05
        if significant and practical:
            c["verdict"] = "подтверждено"
        elif significant:
            c["verdict"] = "значимо, практически мало"
        else:
            c["verdict"] = "не подтверждено"

    # Точечные оценки k=10 на всей A (должны совпасть с results/metrics.csv)
    point = {name: metrics(predict_knn(train, test[name], k=10), test[name][:, 6]) for name in SAMPLES}
    for name in SAMPLES:
        csv_rows.append({
            "variant": "point_k10_full_A",
            "sample": name,
            "metric": "sigma_nmad",
            "seed": "",
            "estimate": point[name]["sigma_nmad"],
            "low": "",
            "high": "",
        })

    # ===== Запись CSV =====
    csv_path = RES / "uncertainty.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["variant", "sample", "metric", "seed", "estimate", "low", "high"])
        w.writeheader()
        for row in csv_rows:
            w.writerow(row)
    print(f"\nЗаписано {len(csv_rows)} строк в {csv_path}")

    # ===== Запись MD =====
    md_path = RES / "uncertainty.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# Результаты эксперимента на неопределённость\n\n")

        # Таблица 1: вариант — σ_NMAD — σ по 5 подвыборкам — 95%-интервал — вывод
        f.write("## Таблица 1: σ_NMAD, kNN k=10\n\n")
        f.write("σ_NMAD — точечная оценка, обучение на всей A (совпадает с results/metrics.csv); "
                "подвыборки — 5 × 80% A (seed 0–4); интервал — бутстреп по галактикам, seed 0.\n\n")
        f.write("| выборка | σ_NMAD | среднее ± σ по 5 подвыборкам | 95%-интервал | устойчивость между seed 0–4 |\n")
        f.write("|---|---|---|---|---|\n")
        for name in SAMPLES:
            ss = subsample_summary[name]
            iv = galaxy_intervals[name]["sigma_nmad"]
            stability_name = "устойчив" if stability_ok else "неустойчив"
            f.write(f"| {name} | {point[name]['sigma_nmad']:.6f} | {ss['sigma_mean']:.6f} ± {ss['sigma_std']:.6f} | "
                    f"[{iv['low']:.6f}, {iv['high']:.6f}] | {stability_name} |\n")

        f.write(f"\n## Таблица 2: Сравнения Δσ_NMAD ({len(comparisons)} сравнений, поправка Холма на все)\n\n")
        f.write("Правило: подтверждено, если p_Холм < 0.05 и весь 95%-интервал Δ дальше 0.005 от нуля. "
                f"p = 0 при {n_boot} повторах записано как «< {1 / n_boot:g}».\n\n")
        f.write("| сравнение | бутстреп | Δ | 95%-интервал | p | p_Холм | вердикт |\n")
        f.write("|---|---|---|---|---|---|---|\n")
        m_cmp = len(comparisons)
        for c in comparisons:
            f.write(f"| {c['pair']} | {c['kind']} | {c['delta']:.6f} | [{c['low']:.6f}, {c['high']:.6f}] | "
                    f"{fmt_p(c['p'], 1 / n_boot)} | {fmt_p(c['p_holm'], m_cmp / n_boot)} | {c['verdict']} |\n")

        f.write("\n## Проверка устойчивости концов интервала σ_NMAD (seeds 0–4)\n\n")
        if stability_ok:
            f.write("Все концы интервалов σ_NMAD между seeds 0–4 расходятся ≤ 0.001 → **устойчиво**.\n")
        else:
            f.write("Расхождение > 0.001 → **неустойчиво**, увеличено n_boot до 5000.\n")

        f.write("\n## Базовые линии на B\n\n")
        f.write("| метод | σ_NMAD | 95%-интервал (seed 0) |\n")
        f.write("|---|---|---|\n")
        f.write(f"| kNN k=10 | {point['B']['sigma_nmad']:.6f} | [{galaxy_intervals['B']['sigma_nmad']['low']:.6f}, "
                f"{galaxy_intervals['B']['sigma_nmad']['high']:.6f}] |\n")
        f.write(f"| kNN k=1 | {k1_b['sigma_full']:.6f} | [{k1_b['sigma_low']:.6f}, {k1_b['sigma_high']:.6f}] |\n")
        f.write(f"| константа (медиана z_spec A) | {const_b['sigma_nmad']:.6f} | — |\n")

    print(f"Записано {md_path}")
    print("Готово.")


if __name__ == "__main__":
    main()