import os
import math
import argparse
import string
import msvcrt
import pandas as pd
import matplotlib.pyplot as plt
from itertools import cycle, product

KEYS = string.digits + string.ascii_lowercase
PAGE_SIZE = len(KEYS)
POSSIBLE_COLORS = ["black", "blue", "red", "green", "orange", "purple"]
POSSIBLE_SYMBOLS = [".", "+", "x", "o", "^", "s"]


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def get_key():
    return msvcrt.getch().decode().lower()


def menu(options, title, multi=False, highlight_idx=None):
    options = list(options)
    selected = [False] * len(options)
    cursor, page = 0, 0
    pages = (len(options) + PAGE_SIZE - 1) // PAGE_SIZE
    while True:
        clear()
        start, end = page * PAGE_SIZE, min((page + 1) * PAGE_SIZE, len(options))
        print(f"{title}\n")
        for i, opt in enumerate(options[start:end]):
            gi = start + i
            mark = (
                "*"
                if (multi and selected[gi]) or (not multi and gi == cursor)
                else " "
            )
            hl = " [x-axis]" if gi == highlight_idx else ""
            print(f"{KEYS[i]}) {mark} {opt}{hl}")
        if pages > 1:
            print("\n[n] next page   [b] back page   [enter] confirm")
        k = get_key()
        if k in ("\r", "\n"):
            return [i for i, s in enumerate(selected) if s] if multi else cursor
        if k == "n" and page < pages - 1:
            page += 1
            continue
        if k == "b" and page > 0:
            page -= 1
            continue
        if k in KEYS[: end - start]:
            gi = start + KEYS.index(k)
            if multi:
                selected[gi] = not selected[gi]
            else:
                cursor = gi


def style_iter():
    return cycle(product(POSSIBLE_SYMBOLS, POSSIBLE_COLORS))


def build_data_dict(df, cols, x_idx, y_idx, sty_iter):
    return {
        "x": (cols[x_idx], df.iloc[:, df.columns.get_loc(cols[x_idx])]),
        "y": [
            (
                cols[i],
                (*next(sty_iter), "scatter", 30),
                df.iloc[:, df.columns.get_loc(cols[i])],
            )
            for i in y_idx
        ],
    }


def plot_from_dict(ax, data, title=None):
    x_lab, x_vals = data["x"]
    for y_lab, (sym, colr, _, size), y_vals in data["y"]:
        ax.scatter(x_vals, y_vals, marker=sym, color=colr, s=size, label=y_lab)
    ax.set_xlabel(x_lab)
    ax.grid(True)
    ax.legend()
    if title:
        ax.set_title(title)


def main():
    ap = argparse.ArgumentParser(description="CSV interactive selector")
    ap.add_argument("csv_path")
    args = ap.parse_args()

    df = pd.read_csv(args.csv_path)
    cols = sorted(df.columns.tolist())

    possible_filter_fields = sorted(
        [
            c
            for c in cols
            if df[c].dtype == "object" or df[c].dtype.name == "string"
        ]
    )
    chosen_field_idx = menu(
        possible_filter_fields,
        "Filter columns (toggle, Enter for none):",
        multi=True,
    )

    chosen_combos = []
    for idx in chosen_field_idx:
        field = possible_filter_fields[idx]
        vals = sorted(map(str, df[field].dropna().unique().tolist()))
        val_idx = menu(
            vals,
            f'Values for "{field}" (toggle, Enter to confirm):',
            multi=True,
        )
        for vi in val_idx:
            chosen_combos.append((field, vals[vi]))

    if not chosen_combos:
        chosen_combos.append((None, None))

    x_idx = menu(cols, "Select X column (Enter to confirm):")
    y_idx = menu(
        cols,
        "Select Y columns (toggle, Enter to confirm):",
        multi=True,
        highlight_idx=x_idx,
    )

    n_plots = len(chosen_combos)
    n_cols = math.ceil(math.sqrt(n_plots))
    n_rows = math.ceil(n_plots / n_cols)

    fig, axes = plt.subplots(
        n_rows,
        n_cols,
        figsize=(4 * n_cols, 4 * n_rows),
        squeeze=False,
    )
    sty_iter = style_iter()

    for (field, val), ax in zip(chosen_combos, axes.flatten()):
        if field is None:
            sub_df = df
            title = "All data"
        else:
            sub_df = df[df[field].astype(str) == val]
            title = f"{field}: {val}"
        data_dict = build_data_dict(sub_df, cols, x_idx, y_idx, sty_iter)
        plot_from_dict(ax, data_dict, title=title)

    # turn off any unused axes
    for ax in axes.flatten()[len(chosen_combos) :]:
        ax.axis("off")

    fig.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
