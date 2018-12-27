#!/usr/bin/python
# -*-coding:utf-8-*-
from os.path import expanduser
from misc import int_rgb2tuple, try_int, list_get, format_rgb, val2rgb_gradient
import json
import pandas as pd
import numpy as np
import argparse

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


def count_keypresses(layout, keystat):
    #count_keys = 0
    a = DEFAULT_A
    for i, line in enumerate(layout):
        if isinstance(line, list):
            for j, p in enumerate(line):
                if isinstance(p, dict):
                    a = p.get('a', a)
                elif isinstance(p, str):
                    d_p = decomp_label(a, p)
                    #count_keys += 1
                    cnt = 0
                    hand = d_p[HAND_IDX]

                    for idx, k in enumerate(d_p[LEGENDS_IDXS]):
                        if k:
                            for s_k in k.split(" "):
                                legend_cnt = 0
                                s_k = s_k.upper()

                                s = keystat[(keystat.symbol == s_k)]
                                if s.values.size == 0:
                                    for iso_gr, iso_idxs in enumerate(ISO_GR_IDXS):
                                        if idx in iso_idxs:
                                            s = keystat[(keystat.repr == s_k) &
                                                        (keystat.iso_next_group == iso_gr)]
                                            break

                                if s.values.size > 0:
                                    legend_cnt = s.cnt.values.sum()
                                    cnt += legend_cnt

                                for fn_abbr_idx, idxs in FN_IDXS:
                                    if idx in idxs:
                                        fn_abbr = d_p[fn_abbr_idx]
                                        if fn_abbr in FN_PARAMS:
                                            FN_PARAMS[fn_abbr]["counter"] += legend_cnt
                                            break

                                if s_k in FN_NAMES2ABBREV:
                                    abbrev = FN_NAMES2ABBREV[s_k]
                                    FN_PARAMS[abbrev]["i"] = i
                                    FN_PARAMS[abbrev]["j"] = j
                                    FN_PARAMS[abbrev]["a"] = a


                    c = try_int(list_get(d_p, COUNTER_IDX, 0))
                    d_p[COUNTER_IDX] = cnt + c
                    layout[i][j] = comp_label(a, d_p)

    for fn, params in FN_PARAMS.items():
        if all(v is not None for v in params.values()):
            i, j, a, counter = params["i"], params["j"], params["a"], params["counter"]
            d_p = decomp_label(a, layout[i][j])
            c = try_int(list_get(d_p, COUNTER_IDX, 0))
            d_p[COUNTER_IDX] = counter + c
            layout[i][j] = comp_label(a, d_p)

    return layout

def calc_min_max_keypresses(layout, keystat):
    minval = keystat.cnt.min()
    maxval = keystat.cnt.max()
    #minval = None
    #maxval = None
    #a = DEFAULT_A
    #for i, line in enumerate(layout):
    #    if isinstance(line, list):
    #        for j, p in enumerate(line):
    #            if isinstance(p, dict):
    #                a = p.get('a', a)
    #            elif isinstance(p, str):
    #                d_p = decomp_label(a, p)

    #                c = try_int(list_get(d_p, COUNTER_IDX, 0))
    #                minval = min(c, minval) if minval is not None else c
    #                maxval = max(c, maxval) if maxval is not None else c
    return minval, maxval

def color_keys(layout, minval, maxval):
    a = DEFAULT_A
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
                    c = try_int(list_get(d_p, COUNTER_IDX, 0))
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
    return layout


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

### Globals, need to plase them in settings file

#gradient_colors = [0x00bab4, 0xCCD100, 0xFF0000] # cayan, green, yellow, red
#gradient_colors = [0xcccccc,0x00FFFF, 0x00FF00, 0xFFFF00, 0xFF0000, 0xFF0000] # toxic rainbow
gradient_colors = [0xcccccc,0xFEEB65, 0xE4521B, 0xcd2f2c] # pretty yellow orange orange red
#gradient_colors = [0xcccccc, 0xFFD100, 0xcb2f2a]          #        yellow orange red
#gradient_colors = [0xFFFFFF, 0x606060, 0x404040] # grayscale
#gradient_colors = [0xcccccc, 0xffe08d, 0xf9cd31,0xf9cd31, 0xff6d1a] # mine keycaps
gradient_colors = list(map(int_rgb2tuple, gradient_colors))

DEFAULT_A = 4
HAND_IDX = 9
COUNTER_IDX = 10

LEGENDS_IDXS = slice(0, 9)
ISO_GR_IDXS = [[0, 1, 2],
               [3, 4, 5]]

FN_IDXS = [[9,  [0, 3, 6]],
           [11, [2, 5, 8]]]

FN_NAMES2ABBREV = {
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

FN_ABBREV2NAMES = {v: k for k, v in FN_NAMES2ABBREV.items()}

FN_PARAMS = {abbrev: {"i": None, "j": None, "a": None, "counter": 0}
             for abbrev in FN_ABBREV2NAMES}

### Globals end

def main():
    stat_path, layout_path, output_path = parse_args()

    keystat = read_keystat(stat_path)
    layout = read_layout(layout_path)

    layout = count_keypresses(layout, keystat)
    minval, maxval = calc_min_max_keypresses(layout, keystat)
    layout = color_keys(layout, minval, maxval)

    write_heatmap(layout, output_path)


if __name__ == "__main__":
    main()
