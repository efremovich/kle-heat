#!/usr/bin/python
# -*-coding:utf-8-*-
from functools import partial
from os.path import expanduser
from collections import namedtuple
import json
import pandas as pd
import numpy as np
import sys
import argparse
EPSILON = sys.float_info.epsilon


def constrain(a, b, x):
    """Constrains a number to be within a range."""
    return min(b, max(a, x))


def remap(in_min, in_max, out_min, out_max, x):
    """Re-maps a number from one range to another.
    That is, a value of fromLow would get mapped to toLow,
    a value of fromHigh to toHigh, values in-between
    to values in-between, etc."""
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;


def try_int(default, *args):
    try:
        return int(*args)
    except (ValueError, TypeError) as e:
        return default

def list_get(l, idx, default):
    try:
        return l[idx]
    except IndexError:
        return default


def stepped_gradient(minval, maxval, val, colors):
    return colors[int(round(remap(minval, maxval, 0, len(colors) - 1, constrain(minval, maxval, val))))]


def bw_gradient(minval, maxval, val):
    return [remap(minval, maxval, 255, 0, val)]*3


def int_rgb2tuple(c):
    return (c >> 16) & 0xFF, (c >> 8) & 0xFF, c & 0xFF


def val2rgb_gradient(minval, maxval, val, colors):
    val = constrain(minval, maxval, val)
    i_f = float(val - minval) / float(maxval - minval) * (len(colors) - 1)
    i, f = int(i_f // 1), i_f % 1
    if f < EPSILON:
        return colors[i]
    else:
        (r1, g1, b1), (r2, g2, b2) = colors[i], colors[i + 1]
        return (int(r1 + f * (r2 - r1)),
                int(g1 + f * (g2 - g1)),
                int(b1 + f * (b2 - b1)))


def cubehelix(s, r, h, g, l):
    psi = 2 * np.pi * ((s / 3) + (r * l))
    lg = l ** g
    return np.round((((h * lg * ((1 - lg) / 2))
                      * np.array([[-0.14861, 1.78277],
                                  [-0.29227, -0.90649],
                                  [1.97294, 0.0]]))
                     .dot(np.array([[np.cos(psi)],
                                    [np.sin(psi)]]))
                     + lg)
                    * 255).flatten().astype(int).tolist()

# s 2   s (linspace 0 3 36)]                  ;(linspace 1 3 9)
# r 1   r (concat (linspace 1 5 30) (linspace 5 1 30)) ;(concat (linspace 0 5 25) (linspace 5 0 24))
# h 0.5 h (linspace 0 2 30)                   ;(concat (linspace 0 2 10) (linspace 2 0 9))]
# g 1   g (linspace 0.8 1.2 3)


def format_rgb(col):
    return "#%02x%02x%02x" % tuple(col)


def read_keystat(path, sep='\t'):
    keystat = pd.read_csv(path, delimiter=sep, header=0)
    keystat.repr = keystat.repr.map(
                     lambda x:
                       (lambda y: y.upper()
                                  if isinstance(y, str)
                                  else y)(
                       eval(x)))
    keystat.symbol = keystat.symbol.map(lambda x: x.upper())
    return keystat


def read_layout(path):
    with open(path) as f:
        data = json.load(f)
    return data


def write_heatmap(data, path):
    with open(path, 'w') as f:
        json.dump(data, f)


LABEL_MAP = [
    [ 0, 6, 2, 8, 9,11, 3, 5, 1, 4, 7,10], #0 = no centering             0  1  2
    [ 1, 7,-1,-1, 9,11, 4,-1,-1,-1,-1,10], #1 = center x                 3  4  5
    [ 3,-1, 5,-1, 9,11,-1,-1, 4,-1,-1,10], #2 = center y                 6  7  8
    [ 4,-1,-1,-1, 9,11,-1,-1,-1,-1,-1,10], #3 = center x & y             -------
    [ 0, 6, 2, 8,10,-1, 3, 5, 1, 4, 7,-1], #4 = center front (default)   9 10 11
    [ 1, 7,-1,-1,10,-1, 4,-1,-1,-1,-1,-1], #5 = center front & x
    [ 3,-1, 5,-1,10,-1,-1,-1, 4,-1,-1,-1], #6 = center front & y
    [ 4,-1,-1,-1,10,-1,-1,-1,-1,-1,-1,-1], #7 = center front & x & y
]


def decomp_label(a, l):
    r = [''] * 12
    for i, v in zip(LABEL_MAP[a], l.split('\n')):
        if i >= 0:
            r[i] = v
    return r


def comp_label(a, l):
    return '\n'.join(str(l[i]) if i >= 0 else ''
                     for i
                     in LABEL_MAP[a]).rstrip('\n')


def parse_args():
    parser = argparse.ArgumentParser(
        description='Draws heatmap on keyboard-layout-editor json')
    parser.add_argument('-i', action='store', dest='stat_path',
                        help='keystat csv file path; default ~/.keystat.csv',
                        default=expanduser("~") + "/.keystat.csv")
    parser.add_argument(
        '-l',
        action='store',
        dest='layout_path',
        required=True,
        help='keyboard-layout-editor json path')
    parser.add_argument(
        '-o',
        action='store',
        dest='output_path',
        required=True,
        help='result kle json path')
    args = parser.parse_args()
    return args.stat_path, args.layout_path, args.output_path

def main():
    stat_path, layout_path, output_path = parse_args()

    keystat = read_keystat(stat_path)
    layout = read_layout(layout_path)

    #gradient_colors = [0x00bab4, 0xCCD100, 0xFF0000] # cayan, green, yellow, red
    #gradient_colors = [0xcccccc,0x00FFFF, 0x00FF00, 0xFFFF00, 0xFF0000, 0xFF0000] # toxic rainbow
    gradient_colors = [0xcccccc,0xFEEB65, 0xE4521B, 0xcd2f2c] # pretty yellow orange orange red
    #gradient_colors = [0xcccccc, 0xFFD100, 0xcb2f2a]          #        yellow orange red
    #gradient_colors = [0xFFFFFF, 0x606060, 0x404040] # grayscale
    #gradient_colors = [0xcccccc, 0xffe08d, 0xf9cd31,0xf9cd31, 0xff6d1a] # mine keycaps
    gradient_colors = list(map(int_rgb2tuple, gradient_colors))

    default_a = 4
    hand_idx = 9
    counter_idx = 10

    legends_idxs = slice(0, 9)
    iso_gr_idxs = [[0, 1, 2],
                   [3, 4, 5]]

    fn_idxs = [[9,  [0, 3, 6]],
               [11, [2, 5, 8]]]

    fn_names2abbrev = {
        "LOWER"  : "l" ,
        "LOWER_L": "ll",
        "LOWER_R": "lr",
        "RAISE"  : "r" ,
        "RAISE_L": "rl",
        "RAISE_R": "rr",
        "FN"     : "f" ,
        "FN1"    : "f1",
        "FN2"    : "f2",
        "FN3"    : "f3",
        "FN4"    : "f4"}

    fn_abbrev2names = {v: k for k, v in fn_names2abbrev.items()}

    fn_params = {abbrev: {"i": None, "j": None, "a": None, "counter": 0}
                 for abbrev in fn_abbrev2names}

    count_keys = 0
    a = default_a
    for i, line in enumerate(layout):
        if isinstance(line, list):
            for j, p in enumerate(line):
                if isinstance(p, dict):
                    a = p.get('a', a)
                elif isinstance(p, str):
                    d_p = decomp_label(a, p)
                    count_keys += 1
                    cnt = 0
                    hand = d_p[hand_idx]

                    for idx, k in enumerate(d_p[legends_idxs]):
                        if k:
                            for s_k in k.split(" "):
                                legend_cnt = 0
                                s_k = s_k.upper()

                                s = keystat[(keystat.symbol == s_k)]
                                if s.values.size == 0:
                                    for iso_gr, iso_idxs in enumerate(iso_gr_idxs):
                                        if idx in iso_idxs:
                                            s = keystat[(keystat.repr == s_k) &
                                                        (keystat.iso_next_group == iso_gr)]
                                            break

                                if s.values.size > 0:
                                    legend_cnt = s.cnt.values.sum()
                                    cnt += legend_cnt

                                for fn_abbr_idx, idxs in fn_idxs:
                                    if idx in idxs:
                                        fn_abbr = d_p[fn_abbr_idx]
                                        if fn_abbr:
                                            fn_params[fn_abbr]["counter"] += legend_cnt

                                if s_k in fn_names2abbrev:
                                    abbrev = fn_names2abbrev[s_k]
                                    fn_params[abbrev]["i"] = i
                                    fn_params[abbrev]["j"] = j
                                    fn_params[abbrev]["a"] = a


                    c = try_int(list_get(d_p, counter_idx, 0))
                    d_p[counter_idx] = cnt + c
                    layout[i][j] = comp_label(a, d_p)

    for fn, params in fn_params.items():
        if all(v is not None for v in params.values()):
            i, j, a, counter = params["i"], params["j"], params["a"], params["counter"]
            d_p = decomp_label(a, layout[i][j])
            c = try_int(list_get(d_p, counter_idx, 0))
            d_p[counter_idx] = counter + c
            layout[i][j] = comp_label(a, d_p)


    minval = keystat.cnt.min()
    maxval = keystat.cnt.max()
    #minval = keystat.cnt.max()
    #maxval = 0
    #a = default_a
    #for i, line in enumerate(layout):
    #    if isinstance(line, list):
    #        for j, p in enumerate(line):
    #            if isinstance(p, dict):
    #                a = p.get('a', a)
    #            elif isinstance(p, str):
    #                d_p = decomp_label(a, p)
    #                c = try_int(list_get(d_p, counter_idx, 0))
    #                minval = min(c, minval)
    #                maxval = max(c, maxval)

    a = default_a
    inserted = False
    cntr = 0
    for i, line in enumerate(layout):
        if isinstance(line, list):
            for j, p in enumerate(line):
                if inserted:
                    inserted = False
                    continue
                if isinstance(p, dict):
                    a = p.get('a', a)
                elif isinstance(p, str):
                    d_p = decomp_label(a, p)
                    c = try_int(list_get(d_p, counter_idx, 0))
                    #col = format_rgb(
                    #    stepped_gradient(
                    #        minval, maxval, c, gradient_colors))
                    col = format_rgb(
                        val2rgb_gradient(
                            minval, maxval, c, gradient_colors))
                    #col = format_rgb(
                    #    val2rgb_gradient(
                    #        0, count_keys, cntr, gradient_colors))
                    #norm_c = constrain(0, 1, cntr/count_keys)
                    #col = format_rgb(cubehelix(0,1,1,0.8,norm_c))
                    layout[i].insert(j, {"c": col})
                    inserted = True
                    cntr += 1

    write_heatmap(layout, output_path)


if __name__ == "__main__":
    main()
