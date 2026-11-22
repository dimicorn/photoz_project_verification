"""Учебный пример к шаблону статьи AI4Science-YSDA 2026.

Задача: y' = lam * y, y(0) = 1 на отрезке [0, 1], точное решение exp(lam * t).
Сравниваются явный метод Эйлера, явный метод средней точки и метод средней
точки с внесённой ошибкой (приращение умножено на h/2 вместо h).
Эмпирический порядок сходимости p = log2(e(h) / e(h/2)) считается по паре
самых мелких шагов h = 2^-9 и h/2 = 2^-10. seed задаёт коэффициент
lam ~ U[-2, -0.5], значения seed 0, 1, 2, 3, 4.

Запуск:     python figures/example_figure.py        подписи на русском языке
            python figures/example_figure.py en     подписи на английском языке
Результат:  figures/example_figure.pdf (рисунок для seed 0)
            и таблица порядков в стандартном выводе.
Окружение:  Python 3, numpy, matplotlib 3.3 и новее
            (проверено: Python 3.10, numpy 1.26, matplotlib 3.9).
"""

import sys
from pathlib import Path

import numpy as np
import matplotlib

matplotlib.use("pdf")
import matplotlib.pyplot as plt  # noqa: E402

SEEDS = range(5)        # число значений seed r = 5
KS = range(4, 11)       # шаги h = 2^-k, k = 4, ..., 10
TOL = 0.05              # критерий принятия: |p - q| <= TOL для каждого seed
OUT = Path(__file__).resolve().parent / "example_figure.pdf"


def euler(lam, y, h):
    return y + h * lam * y


def midpoint(lam, y, h):
    y_half = y + 0.5 * h * lam * y
    return y + h * lam * y_half


def midpoint_bug(lam, y, h):
    y_half = y + 0.5 * h * lam * y
    return y + 0.5 * h * lam * y_half  # внесённая ошибка: h/2 вместо h


# (ключ, шаг метода, заявленный порядок q)
METHODS = [("euler", euler, 1), ("midpoint", midpoint, 2), ("midpoint_bug", midpoint_bug, 2)]


def draw_lambda(seed):
    return np.random.default_rng(seed).uniform(-2.0, -0.5)


def error(step, lam, k):
    n = 2 ** k
    h = 1.0 / n
    y = 1.0
    for _ in range(n):
        y = step(lam, y, h)
    return abs(y - np.exp(lam))


def order(step, lam):
    return np.log2(error(step, lam, KS[-2]) / error(step, lam, KS[-1]))


def table():
    print(f"{'метод':<14} {'q':>3} {'p, среднее':>11} {'ст. откл.':>10}  решение")
    for key, step, q in METHODS:
        p = np.array([order(step, draw_lambda(s)) for s in SEEDS])
        accepted = bool(np.all(np.abs(p - q) <= TOL))
        print(f"{key:<14} {q:>3d} {p.mean():>11.4f} {p.std(ddof=1):>10.1e}  "
              f"{'принято' if accepted else 'отклонено'}   p по значениям seed: {np.round(p, 4)}")


LABELS = {
    "ru": {"euler": "Эйлер", "midpoint": "средняя точка",
           "midpoint_bug": "средняя точка с ошибкой",
           "x": "шаг $h$", "y": "погрешность $e(h)$"},
    "en": {"euler": "Euler", "midpoint": "midpoint",
           "midpoint_bug": "midpoint with error",
           "x": "step $h$", "y": "error $e(h)$"},
}

# Цвета различимы при нарушениях цветового зрения, маркеры и штрих —
# для печати в оттенках серого
STYLE = {"euler": ("#2a78d6", "o", "-"), "midpoint": ("#eb6834", "s", "-"),
         "midpoint_bug": ("#1baf7a", "^", "--")}
INK, INK2, MUTED, GRID = "#0b0b0b", "#52514e", "#898781", "#e1e0d9"


def figure(lang, seed=0):
    plt.rcParams.update({"font.size": 8, "pdf.fonttype": 42,
                         "mathtext.fontset": "dejavusans", "axes.unicode_minus": True})
    lam = draw_lambda(seed)
    h = np.array([2.0 ** -k for k in KS])
    # размер 8,2 x 6,0 см: ширина колонки, рисунок вставляется без масштабирования
    fig, ax = plt.subplots(figsize=(3.23, 2.36))
    fig.subplots_adjust(left=0.16, right=0.97, bottom=0.36, top=0.97)
    for key, step, _ in METHODS:
        color, marker, ls = STYLE[key]
        e = np.array([error(step, lam, k) for k in KS])
        ax.loglog(h, e, ls, color=color, lw=1.5, marker=marker, ms=5,
                  mec="white", mew=0.6, label=LABELS[lang][key], zorder=3)
        if key in ("euler", "midpoint"):
            ref = e[0] * (h / h[0]) ** (1 if key == "euler" else 2) / 3.0
            ax.loglog(h, ref, ":", color=MUTED, lw=1.0, zorder=2)
            ax.annotate(r"$\propto h$" if key == "euler" else r"$\propto h^2$",
                        (h[2], ref[2]), textcoords="offset points", xytext=(4, -10),
                        color=INK2, fontsize=8)
    ax.set_xscale("log", base=2)
    ax.set_xlabel(LABELS[lang]["x"], color=INK)
    ax.set_ylabel(LABELS[lang]["y"], color=INK)
    ax.grid(True, which="major", color=GRID, lw=0.5)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(MUTED)
    ax.tick_params(colors=INK2, which="both")
    ax.legend(loc="upper center", bbox_to_anchor=(0.45, -0.27), ncol=2, frameon=False,
              fontsize=7.5, handlelength=2.4, columnspacing=1.2)
    fig.savefig(OUT, metadata={"Creator": None, "Producer": None, "CreationDate": None})
    plt.close(fig)


if __name__ == "__main__":
    table()
    figure(sys.argv[1] if len(sys.argv) > 1 else "ru")
