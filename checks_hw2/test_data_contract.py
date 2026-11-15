"""Договор о схеме данных Happy: столбцы, типы, диапазоны, ключи.

Запуск: .venv/bin/python checks_hw2/test_data_contract.py

Договор:
  - Разделитель: пробелы
  - Заголовок: # id mag_r u-g g-r r-i i-z z_spec feat1 feat2 feat3 feat4 feat5
  - Столбцы: 0=id(str, 18-19 цифр), 1=mag_r(float), 2-5=цвета(float), 6=z_spec(float), 7-11=feat(float)
  - id: строка из 18–19 цифр (SDSS ObjID)
  - Повторный id допустим, если mag_r, цвета, feat совпадают как строки и |Δz_spec| < 0.001
  - A ∩ B,C,D: 0 общих id и 0 общих строк (mag_r, 4 цвета как строки)
  - C ∩ D: печатает число общих id, на вердикт не влияет
  - Нет NaN и inf
  - mag_r, цвета, feat: печатает min/max (информативно)
  - z_spec: без изменений
"""

import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"

EXPECTED_ROWS = {"A": 74950, "B": 74900, "C": 60315, "D": 74642}
EXPECTED_COLS = 12
EXPECTED_HEADER = "# id mag_r u-g g-r r-i i-z z_spec feat1 feat2 feat3 feat4 feat5"


def load_ids(name):
    """Загрузить id как строки."""
    path = RAW / f"happy_{name}.txt"
    return np.loadtxt(path, dtype=str, usecols=0, comments="#")


def load_data(name):
    """Загрузить данные (все 12 столбцов как float)."""
    path = RAW / f"happy_{name}.txt"
    return np.loadtxt(path, comments="#")


def load_all_str(name):
    """Загрузить все 12 столбцов как строки."""
    path = RAW / f"happy_{name}.txt"
    return np.loadtxt(path, dtype=str, comments="#")


def check_header(name):
    path = RAW / f"happy_{name}.txt"
    with open(path, encoding="utf-8") as f:
        header = f.readline().strip()
    assert header == EXPECTED_HEADER, (
        f"{name}: заголовок '{header}' != '{EXPECTED_HEADER}'"
    )


def check_row_count(name):
    ids = load_ids(name)
    expected = EXPECTED_ROWS[name]
    assert len(ids) == expected, (
        f"{name}: {len(ids)} строк, ожидаем {expected}"
    )


def check_col_count(name):
    data = load_data(name)
    assert data.shape[1] == EXPECTED_COLS, (
        f"{name}: {data.shape[1]} столбцов, ожидаем {EXPECTED_COLS}"
    )


def check_id_format(name):
    """id — строка из 18–19 цифр."""
    ids = load_ids(name)
    for i, iid in enumerate(ids):
        s = str(iid).strip()
        if not (18 <= len(s) <= 19 and s.isdigit()):
            raise AssertionError(
                f"{name}: id[{i}] = '{s}' — не 18–19 цифр"
            )


def check_duplicate_allowed(name):
    """Повторный id допустим, если mag_r, цвета, feat совпадают как строки
    и |Δz_spec| < 0.001. Столбцы 1–5 и 7–11 — как строки."""
    tokens = np.loadtxt(RAW / f"happy_{name}.txt", dtype=str, comments="#")
    ids = tokens[:, 0]
    n_repeated = 0
    groups = defaultdict(list)
    for i, iid in enumerate(ids):
        groups[str(iid)].append(i)
    for iid, indices in groups.items():
        if len(indices) <= 1:
            continue
        n_repeated += 1
        for a in range(len(indices)):
            for b in range(a + 1, len(indices)):
                ia, ib = indices[a], indices[b]
                # columns 1-5 and 7-11 as strings
                row_a = tuple(str(tokens[ia, j]) for j in range(1, 6)) + tuple(str(tokens[ia, j]) for j in range(7, 12))
                row_b = tuple(str(tokens[ib, j]) for j in range(1, 6)) + tuple(str(tokens[ib, j]) for j in range(7, 12))
                # Сначала assert равенства строк (иначе FAIL «разная фотометрия»)
                assert row_a == row_b, (
                    f"{name}: id={iid} : разная фотометрия"
                )
                dz = abs(float(tokens[ia, 6]) - float(tokens[ib, 6]))
                assert dz < 0.001, (
                    f"{name}: дубликат id={iid}, строки совпадают, "
                    f"|Δz_spec|={dz:.4f} >= 0.001"
                )
    print(f"  INFO: {name} повторных id: {n_repeated}")


def check_A_not_in_BCD():
    """A ∩ B,C,D: 0 общих id и 0 общих строк (mag_r, 4 цвета как строки).
    Сравниваем токены-строки из np.loadtxt(dtype=str)."""
    tokens_A = load_all_str("A")
    for name in ["B", "C", "D"]:
        tokens_X = load_all_str(name)
        set_A = set(str(i) for i in tokens_A[:, 0])
        set_X = set(str(i) for i in tokens_X[:, 0])
        common_ids = set_A & set_X
        assert len(common_ids) == 0, (
            f"A ∩ {name}: {len(common_ids)} общих id"
        )
        rows_A = set()
        for i in range(len(tokens_A)):
            row = tuple(str(tokens_A[i, j]) for j in range(1, 6))
            rows_A.add(row)
        rows_X = set()
        for i in range(len(tokens_X)):
            row = tuple(str(tokens_X[i, j]) for j in range(1, 6))
            rows_X.add(row)
        common_rows = rows_A & rows_X
        assert len(common_rows) == 0, (
            f"A ∩ {name}: {len(common_rows)} общих строк (mag_r + цвета)"
        )


def check_C_D_intersection():
    """C ∩ D: печатает число общих id, на вердикт не влияет."""
    ids_C = load_ids("C")
    ids_D = load_ids("D")
    set_C = set(str(i) for i in ids_C)
    set_D = set(str(i) for i in ids_D)
    common = set_C & set_D
    print(f"  INFO: C ∩ D = {len(common)} общих id")


def check_no_nan_inf(name):
    """Нет NaN и inf."""
    data = load_data(name)
    assert np.all(np.isfinite(data)), f"{name}: есть NaN или inf"


def check_all_info(name):
    """Печатает min/max mag_r, цветов, feat одной строкой."""
    data = load_data(name)
    parts = [f"{name}"]
    for col_idx, col_name in [(1, "mag_r"), (2, "u-g"), (3, "g-r"), (4, "r-i"), (5, "i-z")]:
        mn, mx = data[:, col_idx].min(), data[:, col_idx].max()
        parts.append(f"{col_name}=[{mn:.4f},{mx:.4f}]")
    for col_idx in range(7, 12):
        mn, mx = data[:, col_idx].min(), data[:, col_idx].max()
        parts.append(f"feat{col_idx-6}=[{mn:.4f},{mx:.4f}]")
    print(f"  INFO: {' '.join(parts)}")


def check_z_spec_range(name):
    data = load_data(name)
    zs = data[:, 6]
    assert (zs >= 0).all(), f"{name}: есть z_spec < 0"
    assert (zs <= 5).all(), f"{name}: есть z_spec > 5"


if __name__ == "__main__":
    per_sample = [
        ("заголовок", check_header),
        ("число строк", check_row_count),
        ("число столбцов", check_col_count),
        ("id — 18–19 цифр", check_id_format),
        ("повтор id допустим", check_duplicate_allowed),
        ("нет NaN и inf", check_no_nan_inf),
        ("min/max info", check_all_info),
        ("z_spec ∈ [0, 5]", check_z_spec_range),
    ]
    global_tests = [
        ("A ∩ B,C,D = 0", check_A_not_in_BCD),
        ("C ∩ D", check_C_D_intersection),
    ]

    passed = 0
    failed = 0

    for label, test_fn in per_sample:
        try:
            for name in ["A", "B", "C", "D"]:
                test_fn(name)
            print(f"  PASS: {label}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL: {label}: {e}")
            failed += 1
        except Exception as e:
            print(f"  ERROR: {label}: {e}")
            failed += 1

    for label, test_fn in global_tests:
        try:
            test_fn()
            print(f"  PASS: {label}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL: {label}: {e}")
            failed += 1
        except Exception as e:
            print(f"  ERROR: {label}: {e}")
            failed += 1

    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)