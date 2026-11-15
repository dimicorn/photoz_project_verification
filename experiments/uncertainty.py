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


def paired_bootstrap_k10_vs_k1(train, test_data, seed, n_boot):
    """Парный бутстреп: k=10 vs k=1 на одних и тех же индексах test_data."""
    rng = np.random.default_rng(seed)
    n = len(test_data)
    z_phot10 = predict_knn(train, test_data, k=10)
    z_phot1 = predict_knn(train, test_data, k=1)
    zs = test_data[:, 6]

    diffs = []
    for chunk_start in range(0, n_boot, BOOT_CHUNK):
        chunk_size = min(BOOT_CHUNK, n_boot - chunk_start)
        indices = rng.integers(0, n, size=(chunk_size, n))
        for i in range(chunk_size):
            idx = indices[i]
            dz10 = (z_phot10[idx] - zs[idx]) / (1 + zs[idx])
            dz1 = (z_phot1[idx] - zs[idx]) / (1 + zs[idx])
            s10 = float(1.4826 * np.median(np.abs(dz10 - np.median(dz10))))
            s1 = float(1.4826 * np.median(np.abs(dz1 - np.median(dz1))))
            diffs.append(s10 - s1)

    diffs = np.array(diffs)
    return {
        "delta_median": float(np.median(diffs)),
        "delta_low": float(np.percentile(diffs, 2.5)),
        "delta_high": float(np.percentile(diffs, 97.5)),
    }


def holm_correction(p_values, alpha=0.05):
    """Поправка Холма для списка p-значений."""
    p_sorted = np.sort(p_values)
    m = len(p_sorted)
    for i, p in enumerate(p_sorted):
        p_sorted[i] = min(p * (m - i), 1.0)
    # вернуть в исходном порядке
    p_adj = np.zeros_like(p_values)
    idx = np.argsort(np.argsort(p_values))
    for i in range(m):
        p_adj[idx[i]] = p_sorted[i]
    return p_adj


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

    paired = paired_bootstrap_k10_vs_k1(train, test["B"], seed=0, n_boot=n_boot)
    print(f"  Δσ_NMAD (k=10 − k=1): {paired['delta_median']:.6f} [{paired['delta_low']:.6f}, {paired['delta_high']:.6f}]")
    csv_rows.append({
        "variant": "paired_k10_vs_k1",
        "sample": "B",
        "metric": "delta_sigma_nmad",
        "seed": 0,
        "estimate": paired["delta_median"],
        "low": paired["delta_low"],
        "high": paired["delta_high"],
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
    comparisons = []
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
        # p-value: p = 2·min(доля ≤0, доля ≥0)
        frac_le0 = float(np.mean(deltas <= 0))
        frac_ge0 = float(np.mean(deltas >= 0))
        p_val = 2.0 * min(frac_le0, frac_ge0)

        comparisons.append({
            "pair": f"{name1}−{name2}",
            "delta": delta_median,
            "low": delta_low,
            "high": delta_high,
            "p": p_val,
        })
        print(f"  {name1}−{name2}: Δ={delta_median:.6f} [{delta_low:.6f}, {delta_high:.6f}], p={p_val:.4f}")
        csv_rows.append({
            "variant": "hypothesis_delta",
            "sample": f"{name1}-{name2}",
            "metric": "delta_sigma_nmad",
            "seed": 0,
            "estimate": delta_median,
            "low": delta_low,
            "high": delta_high,
        })

    # Поправка Холма
    p_vals = np.array([c["p"] for c in comparisons])
    p_holm = holm_correction(p_vals)
    for c, ph in zip(comparisons, p_holm):
        c["p_holm"] = ph
        practical = abs(c["delta"]) > 0.005
        significant = ph < 0.05
        if significant and practical:
            c["verdict"] = "подтверждено"
        elif significant:
            c["verdict"] = "значимо, практически мало"
        else:
            c["verdict"] = "не подтверждено"

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
        f.write("## Таблица 1: σ_NMAD по подвыборкам и бутстрепу\n\n")
        f.write("| вариант | σ_NMAD | σ по 5 подвыборкам | 95%-интервал | вывод |\n")
        f.write("|---|---|---|---|---|\n")
        for name in SAMPLES:
            # σ по подвыборкам
            ss = subsample_summary[name]
            subsample_str = f"{ss['sigma_std']:.6f}"
            # 95% интервал из galaxy_bootstrap seed 0
            iv = galaxy_intervals[name]["sigma_nmad"]
            interval_str = f"[{iv['low']:.6f}, {iv['high']:.6f}]"
            # Вывод: совпадают ли концы интервалов между seeds?
            stability_name = "устойчив" if stability_ok else "неустойчив"
            f.write(f"| {name} | {ss['sigma_mean']:.6f} | ±{subsample_str} | {interval_str} | {stability_name} |\n")

        f.write("\n## Таблица 2: Сравнения Δσ_NMAD\n\n")
        f.write("| пара | Δ | 95%-интервал | p | p_Холм | вердикт |\n")
        f.write("|---|---|---|---|---|---|\n")
        for c in comparisons:
            f.write(f"| {c['pair']} | {c['delta']:.6f} | [{c['low']:.6f}, {c['high']:.6f}] | {c['p']:.4f} | {c['p_holm']:.4f} | {c['verdict']} |\n")

        f.write("\n## Проверка устойчивости концов интервала σ_NMAD (seeds 0–4)\n\n")
        if stability_ok:
            f.write("Все концы интервалов σ_NMAD между seeds 0–4 расходятся ≤ 0.001 → **устойчиво**.\n")
        else:
            f.write("Расхождение > 0.001 → **неустойчиво**, увеличено n_boot до 5000.\n")

        f.write("\n## Базовые линии на B\n\n")
        f.write(f"| метод | σ_NMAD |\n")
        f.write(f"|---|---|\n")
        f.write(f"| k=1 (полные данные) | {k1_b['sigma_full']:.6f} |\n")
        f.write(f"| k=1 | {k1_b['sigma_nmad']:.6f} [{k1_b['sigma_low']:.6f}, {k1_b['sigma_high']:.6f}] |\n")
        f.write(f"| константа (медиана z_spec A) | {const_b['sigma_nmad']:.6f} |\n")
        f.write(f"| Δ(k=10 − k=1) | {paired['delta_median']:.6f} [{paired['delta_low']:.6f}, {paired['delta_high']:.6f}] |\n")

    print(f"Записано {md_path}")
    print("Готово.")


if __name__ == "__main__":
    main()