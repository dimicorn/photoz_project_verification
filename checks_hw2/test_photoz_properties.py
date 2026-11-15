"""Свойства kNN photo-z: содержательные проверки корректности расчёта.

Запуск: .venv/bin/python checks_hw2/test_photoz_properties.py

Свойства:
  1. Предсказания — выпуклая комбинация z_spec (в диапазоне обучающей)
  2. Согласованность с независимым kNN (полный перебор numpy, 200 строк, seed 2026)
  3. z_spec в диапазоне [0, 5]
  4. Предсказание = среднее, а не медиана
  5. Порядок строк и id совпадают с raw-файлом (строковое сравнение)
  6. Количество строк совпадает
  7. Аффинная связь feat: feat_j = a_j·x_j + b_j, МНК по A, те же a,b для B,C,D
  8. k=1 на A: z_phot = z_spec (self-prediction)
  9. Инвариантность к перестановке строк и сдвигу признаков
"""

import csv
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
RES = ROOT / "results"
K = 10
FEATS = slice(7, 12)
ZCOL = 6


def load(name):
    return np.loadtxt(RAW / f"happy_{name}.txt", comments="#")


def load_raw(name):
    """Загрузить: id как строка, данные как float."""
    path = RAW / f"happy_{name}.txt"
    ids = np.loadtxt(path, dtype=str, usecols=0, comments="#")
    data = np.loadtxt(path, comments="#")
    return ids, data


def predict_knn(train, test, k=K):
    """Полный перебор: евклидово расстояние, среднее z_spec k соседей.
    Считает по кускам по 20 строк проверки; квадрат расстояния; stable sort."""
    train_feats = train[:, FEATS]
    test_feats = test[:, FEATS]
    n_test = len(test_feats)
    z_phot = np.empty(n_test)
    chunk = 20
    for start in range(0, n_test, chunk):
        end = min(start + chunk, n_test)
        diff = test_feats[start:end, np.newaxis, :] - train_feats[np.newaxis, :, :]
        dists_sq = (diff ** 2).sum(-1)
        nn_idx = np.argsort(dists_sq, kind="stable")[:, :k]
        z_phot[start:end] = train[nn_idx, ZCOL].mean(axis=1)
    return z_phot


def load_predictions(name):
    path = RES / f"predictions_{name}.csv"
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    ids = np.array([r["id"] for r in rows])  # строки
    zs = np.array([float(r["z_spec"]) for r in rows])
    zp = np.array([float(r["z_phot"]) for r in rows])
    return ids, zs, zp


# ============================================================
# СВОЙСТВО 1: Предсказания — в диапазоне обучающей выборки
# ============================================================
def test_predictions_in_range():
    """z_phot ∈ [min(z_spec_train), max(z_spec_train)] для всех галактик."""
    train = load("A")
    z_min, z_max = train[:, ZCOL].min(), train[:, ZCOL].max()
    for name in ["B", "C", "D"]:
        _, _, zp = load_predictions(name)
        assert zp.min() >= z_min - 1e-10, (
            f"{name}: z_phot.min()={zp.min():.6f} < z_spec.min()={z_min:.6f}"
        )
        assert zp.max() <= z_max + 1e-10, (
            f"{name}: z_phot.max()={zp.max():.6f} > z_spec.max()={z_max:.6f}"
        )


# ============================================================
# СВОЙСТВО 2: Согласованность с независимым kNN (полный перебор numpy)
# ============================================================
def test_predictions_match_independent_knn():
    """z_phot из файла совпадает с полным перебором numpy до 1e-9."""
    train = load("A")
    rng = np.random.RandomState(2026)
    for name in ["B", "C", "D"]:
        data = load(name)
        _, _, zp = load_predictions(name)
        n = len(data)
        idx = rng.choice(n, size=min(200, n), replace=False)
        ref = predict_knn(train, data[idx], K)
        diff = np.abs(ref - zp[idx])
        assert diff.max() < 1e-9, (
            f"{name}: max|z_phot − kNN| = {diff.max():.2e}"
        )


# ============================================================
# СВОЙСТВО 3: z_spec в проверочных выборках — в диапазоне [0, 5]
# ============================================================
def test_z_spec_range():
    """z_spec ∈ [0, 5] для всех галактик в проверочных выборках."""
    for name in ["B", "C", "D"]:
        data = load(name)
        zs = data[:, ZCOL]
        assert (zs >= 0).all(), f"{name}: есть z_spec < 0"
        assert (zs <= 5).all(), f"{name}: есть z_spec > 5"


# ============================================================
# СВОЙСТВО 4: Предсказание = среднее, а не медиана
# ============================================================
def test_knn_is_mean_not_median():
    """Предсказание = среднее z_spec соседей, а не медиана.
    200 случайных строк B (seed 2026), как в test_predictions_match_independent_knn."""
    train = load("A")
    data = load("B")
    rng = np.random.RandomState(2026)
    n = len(data)
    idx = rng.choice(n, size=min(200, n), replace=False)
    ref_mean = predict_knn(train, data[idx], K)
    train_feats = train[:, FEATS]
    test_feats = data[idx, FEATS]
    diff = test_feats[:, np.newaxis, :] - train_feats[np.newaxis, :, :]
    dists_sq = (diff ** 2).sum(-1)
    nn_idx = np.argsort(dists_sq, kind="stable")[:, :K]
    ref_median = np.median(train[nn_idx, ZCOL], axis=1)

    _, _, zp = load_predictions("B")
    diff_mean = np.abs(ref_mean - zp[idx])
    diff_median = np.abs(ref_median - zp[idx])

    assert diff_mean.max() < 1e-4, "Среднее не совпадает с z_phot"
    assert (diff_median > 1e-6).any(), (
        "Медиана совпадает со средним — возможно, z_phot считается как медиана"
    )


# ============================================================
# СВОЙСТВО 5: Порядок строк и id совпадают с raw-файлом (строки)
# ============================================================
def test_row_order_preserved():
    """id и z_spec в predictions.csv совпадают с raw-файлом по порядку."""
    for name in ["B", "C", "D"]:
        ids_raw, data = load_raw(name)
        ids, zs, _ = load_predictions(name)
        assert np.array_equal(ids, ids_raw), (
            f"{name}: id не совпадает с raw"
        )
        assert np.allclose(zs, data[:, ZCOL]), (
            f"{name}: z_spec не совпадает с raw"
        )


# ============================================================
# СВОЙСТВО 6: Количество строк совпадает
# ============================================================
def test_row_count_matches():
    """Число строк predictions.csv = число строк в raw-файле."""
    for name in ["B", "C", "D"]:
        ids, data = load_raw(name)
        _, _, zp = load_predictions(name)
        assert len(zp) == len(data), (
            f"{name}: {len(zp)} строк в predictions, {len(data)} в raw"
        )


# ============================================================
# СВОЙСТВО 7: Аффинная связь feat: feat_j = a_j·x_j + b_j
# МНК по A, те же a,b для B,C,D, невязка ≤ 2e-5
# ============================================================
def test_features_affine():
    """feat_j = a_j·x_j + b_j, МНК по A, те же a,b для B,C,D.
    x = столбец 1+j (mag_r, u-g, g-r, r-i, i-z), y = столбец 7+j (feat1..feat5)."""
    train = load("A")
    for j in range(5):  # feat1..feat5
        x_train = train[:, 1 + j]  # mag_r, u-g, g-r, r-i, i-z
        y_train = train[:, 7 + j]  # feat1..feat5
        A_mat = np.vstack([x_train, np.ones(len(x_train))]).T
        a, b = np.linalg.lstsq(A_mat, y_train, rcond=None)[0]
        mu = -b / a
        sigma = 1.0 / a
        print(f"  INFO: feat{j+1}: a={a:.6f}, b={b:.6f}, mu={mu:.6f}, sigma={sigma:.6f}")
        for name in ["A", "B", "C", "D"]:
            data = load(name)
            x = data[:, 1 + j]
            y = data[:, 7 + j]
            residual = np.max(np.abs(y - (a * x + b)))
            assert residual <= 2e-5, (
                f"{name} feat{j+1}: невязка МНК = {residual:.2e} > 2e-5"
            )


# ============================================================
# СВОЙСТВО 8: k=1 на A: z_phot = z_spec (self-prediction)
# ============================================================
def test_self_prediction_k1():
    """predict_knn из src/ при k=1 на A: z_phot = z_spec.
    Исключить строки с d[:,1]==0 (другой объект на нулевом расстоянии)."""
    sys.path.insert(0, str(ROOT))
    from src.photoz import predict_knn as predict_knn_src
    from scipy.spatial import cKDTree
    train = load("A")
    tree = cKDTree(train[:, FEATS])
    d, _ = tree.query(train[:, FEATS], k=2)
    mask = d[:, 1] != 0
    n_excluded = (~mask).sum()
    print(f"  INFO: self_prediction_k1: исключено {n_excluded} строк с d[:,1]==0")
    z_self = predict_knn_src(train, train, k=1)
    z_spec = train[:, ZCOL]
    diffs = np.abs(z_self[mask] - z_spec[mask])
    assert np.all(diffs < 1e-10), (
        f"Не все z_self == z_spec: max diff = {diffs.max():.2e}"
    )


# ============================================================
# СВОЙСТВО 9: Инвариантность к перестановке и сдвигу
# ============================================================
def test_invariance():
    """predict_knn не меняется от перестановки строк и сдвига признаков на 3.7."""
    sys.path.insert(0, str(ROOT))
    from src.photoz import predict_knn as predict_knn_src
    rng_perm = np.random.RandomState(7)
    train = load("A")
    rng = np.random.RandomState(11)
    B = load("B")
    idx = rng.choice(len(B), 2000, replace=False)
    test = B[idx]

    perm = rng_perm.permutation(len(train))
    z1 = predict_knn_src(train, test, K)
    z2 = predict_knn_src(train[perm], test, K)
    assert np.abs(z1 - z2).max() < 1e-9, "Не инвариантно к перестановке"

    shift = 3.7
    train_shifted = train.copy()
    train_shifted[:, FEATS] += shift
    test_shifted = test.copy()
    test_shifted[:, FEATS] += shift
    z3 = predict_knn_src(train_shifted, test_shifted, K)
    assert np.abs(z1 - z3).max() < 1e-9, "Не инвариантно к сдвигу"


if __name__ == "__main__":
    tests = [
        test_predictions_in_range,
        test_predictions_match_independent_knn,
        test_z_spec_range,
        test_knn_is_mean_not_median,
        test_row_order_preserved,
        test_row_count_matches,
        test_features_affine,
        test_self_prediction_k1,
        test_invariance,
    ]
    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS: {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL: {t.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"  ERROR: {t.__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)