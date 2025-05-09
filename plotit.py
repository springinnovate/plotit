import os
import argparse
import string
import msvcrt
import pandas as pd
import matplotlib.pyplot as plt
from itertools import cycle
from itertools import product

KEYS = string.digits + string.ascii_lowercase
PAGE_SIZE = len(KEYS)
POSSIBLE_COLORS = ["black", "blue", "red", "green", "orange", "purple"]
POSSIBLE_SYMBOLS = [".", "+", "x", "o", "^", "s"]
STYLE_ITER = cycle(product(POSSIBLE_SYMBOLS, POSSIBLE_COLORS))


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def get_key():
    return msvcrt.getch().decode().lower()


def menu(options, title, multi=False, highlight_idx=None):
    options = list(options)  # ensure indexable
    selected = [False] * len(options)
    cursor = 0
    page = 0
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


def plot_from_dict(data, graph_title=None, grid=False):
    x_label, x_vals = data["x"]
    fig, ax = plt.subplots()
    for y_label, (style, color, ptype, size), y_vals in data["y"]:
        if ptype == "line":
            ax.plot(
                x_vals,
                y_vals,
                linestyle=style,
                color=color,
                linewidth=size,
                label=y_label,
            )
        else:
            ax.scatter(
                x_vals, y_vals, marker=style, color=color, s=size, label=y_label
            )
    ax.set_xlabel(x_label)
    ax.grid(grid)
    ax.legend()
    fig.tight_layout()
    if graph_title:
        ax.set_title(graph_title)
    return fig, ax


def main():
    ap = argparse.ArgumentParser(description="CSV interactive selector")
    ap.add_argument("csv_path")
    args = ap.parse_args()

    df = pd.read_csv(args.csv_path)
    cols = sorted(df.columns.tolist())  # alphabetical

    # only filter fields that are strings
    possible_filter_fields = sorted(
        [
            col
            for col in cols
            if df[col].dtype == "object" or df[col].dtype.name == "string"
        ]
    )
    chosen_filter_field_indexes = menu(
        possible_filter_fields,
        "Filter columns (toggle, Enter for none):",
        multi=True,
    )

    # filter the values for those chosen fields
    df_by_field = {
        possible_filter_fields[f_idx]: df.copy()
        for f_idx in chosen_filter_field_indexes
    }
    filter_values_by_field = {}
    for f_idx in chosen_filter_field_indexes:
        field = possible_filter_fields[f_idx]
        vals = sorted(map(str, df[field].dropna().unique().tolist()))
        chosen_vals = menu(
            vals,
            f'Values for "{field}" (toggle, Enter to confirm):',
            multi=True,
        )
        if chosen_vals:
            local_df = df_by_field[field]
            df_by_field[field] = local_df[
                local_df[field].astype(str).isin([vals[i] for i in chosen_vals])
            ]
            # get string representation of those values
            filter_values_by_field[field] = [vals[idx] for idx in chosen_vals]
    x_idx = menu(cols, "Select X column (Enter to confirm):")
    y_idx = menu(
        cols,
        "Select Y columns (toggle, Enter to confirm):",
        multi=True,
        highlight_idx=x_idx,
    )

    for f_idx in chosen_filter_field_indexes:
        field = possible_filter_fields[f_idx]
        local_df = df_by_field[field]
        data_dict = {
            "x": (
                cols[x_idx],
                local_df.iloc[:, local_df.columns.get_loc(cols[x_idx])],
            ),
            "y": [
                (
                    cols[i],
                    (*next(STYLE_ITER), "scatter", 30),
                    local_df.iloc[:, local_df.columns.get_loc(cols[i])],
                )
                for i in y_idx
            ],
        }

        clear()
        filter_values = filter_values_by_field[field]
        subtitle = ", ".join(filter_values) if filter_values else "All"
        graph_title = f"{field}: {subtitle}"

        plot_from_dict(data_dict, graph_title=graph_title, grid=True)
        plt.show()


if __name__ == "__main__":
    main()
