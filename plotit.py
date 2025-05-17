import argparse
import math
import os
import string
import sys
from itertools import cycle, product
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import yaml
import msvcrt

KEYS = string.digits + string.ascii_lowercase  # 36 per page
PAGE = len(KEYS)
COLORS = ["black", "blue", "red", "green", "orange", "purple"]
SYMBOLS = [".", "+", "x", "o", "^", "s"]
STYLE_CYCLE = cycle(product(SYMBOLS, COLORS))


def clear():
    return os.system("cls" if os.name == "nt" else "clear")


def getkey():
    return msvcrt.getch().decode().lower()


def menu(items, title, multi=False, highlight=None):
    sel, cur, page, pages = (
        [False] * len(items),
        0,
        0,
        (len(items) + PAGE - 1) // PAGE,
    )
    while True:
        clear()
        start, end = page * PAGE, min((page + 1) * PAGE, len(items))
        print(f"{title}\n")
        for i, item in enumerate(items[start:end]):
            gi = start + i
            mark = "*" if (multi and sel[gi]) or (not multi and gi == cur) else " "
            hl = " [x-axis]" if gi == highlight else ""
            print(f"{KEYS[i]}) {mark} {item}{hl}")
        if pages > 1:
            print("\n[n] next  [b] back  [enter] confirm")
        k = getkey()
        if k in ("\r", "\n"):
            return [i for i, s in enumerate(sel) if s] if multi else cur
        if k == "n" and page < pages - 1:
            page += 1
            continue
        if k == "b" and page > 0:
            page -= 1
            continue
        if k in KEYS[: end - start]:
            gi = start + KEYS.index(k)
            sel[gi] = not sel[gi] if multi else sel[gi]
            cur = gi


def style_iter():
    return cycle(product(SYMBOLS, COLORS))


def build_data(df, cols, x_col, y_cols, sty):
    return {
        "x": (x_col, df[x_col]),
        "y": [(c, (*next(sty), "scatter", 30), df[c]) for c in y_cols],
    }


def plot_ax(ax, data, title):
    x_lab, x_vals = data["x"]
    for y_lab, (sym, col, _, size), y_vals in data["y"]:
        ax.scatter(x_vals, y_vals, marker=sym, color=col, s=size, label=y_lab)
    ax.set_xlabel(x_lab)
    ax.set_title(title)
    ax.grid(True)
    ax.legend()


# ─── Interactive configuration ───────────────────────────────────────────────
def interactive_config(csv_path):
    df = pd.read_csv(csv_path, usecols=lambda c: not c.strip().startswith("Unnamed"))
    print(df.columns)

    cols = sorted(df.columns)

    # choose filter fields & values
    str_cols = [
        c for c in cols if df[c].dtype == "object" or df[c].dtype.name == "string"
    ]
    field_idx = menu(str_cols, "Filter columns (toggle, enter for none):", multi=True)
    filters = {}
    for i in field_idx:
        c = str_cols[i]
        vs = sorted(map(str, df[c].dropna().unique()))
        vi = menu(vs, f'Values for "{c}" (toggle, enter confirm):', multi=True)
        if vi:
            filters[c] = [vs[j] for j in vi]

    # choose axes
    x_idx = menu(cols, "Select X column:", highlight=None)
    y_idx = menu(cols, "Select Y columns (toggle):", multi=True, highlight=x_idx)
    x_col = cols[x_idx]
    y_cols = [cols[i] for i in y_idx]

    return {
        "csv": str(csv_path),
        "filters": filters,
        "x": x_col,
        "y": y_cols,
    }


# ─── Plotting from YAML ───────────────────────────────────────────────────────
def plot_from_yaml(cfg):
    df = pd.read_csv(cfg["csv"], usecols=lambda c: not c.strip().startswith("Unnamed"))
    for col, vals in cfg["filters"].items():
        df = df[df[col].astype(str).isin(vals)]

    combos = (
        [(None, None)]
        if not cfg["filters"]
        else [(col, v) for col, vs in cfg["filters"].items() for v in vs]
    )

    n = len(combos)
    nc = math.ceil(math.sqrt(n))
    nr = math.ceil(n / nc)
    fig, axes = plt.subplots(nr, nc, figsize=(4 * nc, 4 * nr), squeeze=False)
    sty = style_iter()

    for (col, val), ax in zip(combos, axes.flatten()):
        sub = df if col is None else df[df[col].astype(str) == val]
        plot_ax(
            ax,
            build_data(sub, sub.columns, cfg["x"], cfg["y"], sty),
            "All data" if col is None else f"{col}: {val}",
        )
    for ax in axes.flatten()[n:]:
        ax.axis("off")
    fig.tight_layout()
    plt.show()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True, help="CSV to configure or YAML to plot")
    args = ap.parse_args()

    fpath = Path(args.file)
    if fpath.suffix.lower() == ".csv":
        cfg = interactive_config(fpath)
        yaml_path = Path(fpath.stem).with_suffix(".yaml")
        yaml.safe_dump(cfg, open(yaml_path, "w"))
        print(f"\nConfiguration saved to: {yaml_path}")
        plot_from_yaml(cfg)
    elif fpath.suffix.lower() == ".yaml":
        cfg = yaml.safe_load(open(fpath))
        plot_from_yaml(cfg)
    else:
        sys.exit("Provide a .csv or .yaml file to --file")


if __name__ == "__main__":
    main()
