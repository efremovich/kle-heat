#!/usr/bin/python
#-*-coding:utf-8-*-
import json
import pandas as pd
import numpy as np
from functools import partial
from os.path import expanduser
import sys
EPSILON = sys.float_info.epsilon

def constrain(a, b, x):
    """Constrains a number to be within a range."""
    return min(b, max(a, x))

def list_get (l, idx, default):
  try:
    return l[idx]
  except IndexError:
    return default

def val2rgb_gradient(minval, maxval, val, colors):
    val = constrain(minval, maxval, val)
    i_f = float(val-minval) / float(maxval-minval) * (len(colors)-1)
    i, f = int(i_f // 1), i_f % 1
    if f < EPSILON:
        return colors[i]
    else:
        (r1, g1, b1), (r2, g2, b2) = colors[i], colors[i+1]
        return int(r1 + f*(r2-r1)), int(g1 + f*(g2-g1)), int(b1 + f*(b2-b1))

def astro_intensity(s, r, h, g, l):
    psi = 2 * np.pi * ((s / 3) + (r * l))
    lg = l ** g
    return np.round((((h * lg * ((1 - lg)/2))\
                      * np.array([[-0.14861, 1.78277],
                                  [-0.29227, -0.90649],
                                  [1.97294,  0.0]]))\
                     .dot(np.array([[np.cos(psi)],
                                    [np.sin(psi)]]))
                     + lg)
                    * 255).flatten().astype(int).tolist()

# s 2   s (linspace 0 3 36)]                  ;(linspace 1 3 9)
# r 1   r (concat (linspace 1 5 30) (linspace 5 1 30)) ;(concat (linspace 0 5 25) (linspace 5 0 24))
# h 0.5 h (linspace 0 2 30)                   ;(concat (linspace 0 2 10) (linspace 2 0 9))]
# g 1   g (linspace 0.8 1.2 3)

def format_rgb(col):
    return "#%02x%02x%02x"%tuple(col)

def read_keystat(path, sep=", "):
    keystat = pd.read_csv(path, delimiter=sep, header=0, engine='python')
    keystat.repr = keystat.repr.map(lambda x: eval(x))
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
  r = ['']*12
  for i, v in zip(LABEL_MAP[a], l.split('\n')):
    if i >= 0:
      r[i] = v
  return r

def comp_label(a, l):
  return '\n'.join(str(l[i]) if i >= 0 else '' for i in LABEL_MAP[a]).rstrip('\n')

def main():

    json_path = "jianheat.json"
    stat_path = expanduser("~")+"/.keystat.csv"
    heatmap_path = "jianheatmap.json"


    keystat = read_keystat(stat_path)
    layout = read_layout(json_path)


    #minval = keystat.cnt.max()
    #maxval = 0
    minval = keystat.cnt.min()
    maxval = keystat.cnt.max()
    #gradient_colors = [(0xcc, 0xcc, 0xcc), (0xFF,0xFF,0x00), (0xdd,0x11,0x26)]
    #gradient_colors = [(0x00, 0x00, 0xFF), (0x00,0xFF,0x00), (0xFF,0x00,0x00)]
    gradient_colors = [(0x00, 0xba, 0xb4), (0xFF,0xD1,0x00), (0xcb, 0x2f, 0x2a)]
    #gradient_colors = [(0xFF, 0xFF, 0xFF), (0x60,0x60,0x60), (0x40, 0x40, 0x40)]

    a = 4

    r_raise_cnt = 0
    l_raise_cnt = 0
    r_lower_cnt = 0
    l_lower_cnt = 0

    count_keys = 0
    for i, line in enumerate(layout):
      if isinstance(line, list):
        for j, p in enumerate(line):
          if isinstance(p, dict):
            a = p.get('a', a)
          elif isinstance(p, str):
            count_keys += 1
            cnt = 0
            d_p = decomp_label(a, p)
            hand = d_p[9]
            hold = d_p[7]

            for idx, k in enumerate(d_p[:-3]):
              if k:
                for s_k in k.split(" "):
                  s_k = s_k.upper()

                  s = keystat[(keystat.symbol == s_k)]
                  if s.values.size == 0:
                    if idx in [3, 4, 5]:
                      s = keystat[(keystat.repr == s_k) & (keystat.iso_next_group == 1)]
                    elif idx in [0, 1, 2]:
                      s = keystat[(keystat.repr == s_k) & (keystat.iso_next_group == 0)]

                  if s.values.size > 0:
                    cnt += s.cnt.values.sum()

                  if idx in [0, 3, 6] and hand == 'r':
                    l_lower_cnt += cnt
                  elif idx in [2, 5, 8] and hand == 'r':
                    l_raise_cnt += cnt
                  elif idx in [2, 5, 8] and hand == 'l':
                    r_raise_cnt += cnt
                  elif idx in [0, 3, 6] and hand == 'l':
                    r_lower_cnt += cnt


            if hold.upper() == "RAISE" and hand == 'l':
              l_raise_i, l_raise_j, l_raise_a = i, j, a
            elif hold.upper() == "RAISE" and hand == 'r':
              r_raise_i, r_raise_j, r_raise_a = i, j, a
            elif hold.upper() == "LOWER" and hand == 'l':
              l_lower_i, l_lower_j, l_lower_a = i, j, a
            elif hold.upper() == "LOWER" and hand == 'r':
              r_lower_i, r_lower_j, r_lower_a = i, j, a

            c = list_get(d_p, 10, 0)
            c = 0 if c is '' else int(c)
            d_p[10] = cnt + c
            layout[i][j] = comp_label(a, d_p)


    d_p = decomp_label(r_raise_a, layout[r_raise_i][r_raise_j])
    c = list_get(d_p, 10, 0)
    c = 0 if c is '' else int(c)
    d_p[10] = r_raise_cnt + c
    layout[r_raise_i][r_raise_j] = comp_label(r_raise_a, d_p)

    d_p = decomp_label(l_raise_a, layout[l_raise_i][l_raise_j])
    c = list_get(d_p, 10, 0)
    c = 0 if c is '' else int(c)
    d_p[10] = l_raise_cnt + c
    layout[l_raise_i][l_raise_j] = comp_label(l_raise_a, d_p)

    d_p = decomp_label(r_lower_a, layout[r_lower_i][r_lower_j])
    c = list_get(d_p, 10, 0)
    c = 0 if c is '' else int(c)
    d_p[10] = r_lower_cnt + c
    layout[r_lower_i][r_lower_j] = comp_label(r_lower_a, d_p)

    d_p = decomp_label(l_lower_a, layout[l_lower_i][l_lower_j])
    c = list_get(d_p, 10, 0)
    c = 0 if c is '' else int(c)
    d_p[10] = l_lower_cnt + c
    layout[l_lower_i][l_lower_j] = comp_label(l_lower_a, d_p)


   # a = 4
   # for i, line in enumerate(layout):
   #   if isinstance(line, list):
   #     for j, p in enumerate(line):
   #       if isinstance(p, dict):
   #         a = p.get('a', a)
   #       elif isinstance(p, str):
   #         d_p = decomp_label(a, p)
   #         c = list_get(d_p, 10, 0)
   #         c = 0 if c is '' else int(c)
   #         minval = min(c, minval)
   #         maxval = max(c, maxval)


    a = 4
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
            c = list_get(d_p, 10, 0)
            c = 0 if c is '' else int(c)
            col = format_rgb(val2rgb_gradient(minval, maxval, c, gradient_colors))
            #norm_c = constrain(0, 1, c/maxval)
            #col = format_rgb(astro_intensity(0,5,1,0.2,norm_c))
            layout[i].insert(j, {"c": col})
            inserted = True
            cntr += 1

    write_heatmap(layout, heatmap_path)

if __name__ == "__main__":
    main()
