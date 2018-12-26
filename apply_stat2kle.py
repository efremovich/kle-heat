#!/usr/bin/python
#-*-coding:utf-8-*-
import json
import pandas as pd
import numpy as np
from functools import partial
from os.path import expanduser
import sys
EPSILON = sys.float_info.epsilon

def constrain(a, b, x): # надо наверное во внешний модуль, типа misc.py
    """Constrains a number to be within a range."""
    return min(b, max(a, x))

def list_get (l, idx, default): # тоже во внешний модуль, наверное
  try:
    return l[idx]
  except IndexError:
    return default

def val2rgb_gradient(minval, maxval, val, colors): # вычислить градиентовый цвет, тоже во внешний модуль misc.py/colors.py
    val = constrain(minval, maxval, val)
    i_f = float(val-minval) / float(maxval-minval) * (len(colors)-1)
    i, f = int(i_f // 1), i_f % 1
    if f < EPSILON:
        return colors[i]
    else:
        (r1, g1, b1), (r2, g2, b2) = colors[i], colors[i+1]
        return int(r1 + f*(r2-r1)), int(g1 + f*(g2-g1)), int(b1 + f*(b2-b1))

def astro_intensity(s, r, h, g, l): # другая функция для градиента, выдаёт цвета красивее. тоже во внешний модуль misc.py/colors.py
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

#;; s 2
#;; r 1
#;; h 0.5
#;; g 1
#(defn setup-astro-intensity []
#  (q/frame-rate 60)
#  {:show-info {:frame-rate true}
#   :palettes  (cycle
#                (for [g (linspace 0.8 1.2 3)
#                      r (concat (linspace 1 5 30) (linspace 5 1 30)) ;(concat (linspace 0 5 25) (linspace 5 0 24))
#                      h (linspace 0 2 30)                   ;(concat (linspace 0 2 10) (linspace 2 0 9))]
#                      s (linspace 0 3 36)]                  ;(linspace 1 3 9)
#                  (for [l (linspace 0 1 (q/width))]
#                    (astro-intensity s r h g l))))})
#



def format_rgb(col): # форматирует лист из трёх интов в хтмл цвет
    return "#%02x%02x%02x"%tuple(col)

def read_keystat(path, sep=", "): # читает csv со статистикой
    keystat = pd.read_csv(path, delimiter=sep, header=0, engine='python')
    keystat.repr = keystat.repr.map(lambda x: eval(x))
    return keystat

def read_layout(path): # читает json с раскладкой
    with open(path) as f:
        data = json.load(f)
    return data

def write_heatmap(data, path): # записывает json с раскладкой
    with open(path, 'w') as f:
      json.dump(data, f)

LABEL_MAP = [ # карта чтения легенд клавиш в соответствии с выравниванием
  [ 0, 6, 2, 8, 9,11, 3, 5, 1, 4, 7,10], # 0 = no centering             0  1  2
  [ 1, 7,-1,-1, 9,11, 4,-1,-1,-1,-1,10], # 1 = center x                 3  4  5
  [ 3,-1, 5,-1, 9,11,-1,-1, 4,-1,-1,10], # 2 = center y                 6  7  8
  [ 4,-1,-1,-1, 9,11,-1,-1,-1,-1,-1,10], # 3 = center x & y             -------
  [ 0, 6, 2, 8,10,-1, 3, 5, 1, 4, 7,-1], # 4 = center front (default)   9 10 11
  [ 1, 7,-1,-1,10,-1, 4,-1,-1,-1,-1,-1], # 5 = center front & x
  [ 3,-1, 5,-1,10,-1,-1,-1, 4,-1,-1,-1], # 6 = center front & y
  [ 4,-1,-1,-1,10,-1,-1,-1,-1,-1,-1,-1], # 7 = center front & x & y
]
def decomp_label(a, l): # декомпозиция сериализованной легенды клавиши с выравниванием
  r = ['']*12
  for i, v in zip(LABEL_MAP[a], l.split('\n')):
    if i >= 0:
      r[i] = v
  return r

def comp_label(a, l): # сериализация легенды клавиши с выравниванием
  return '\n'.join(str(l[i]) if i >= 0 else '' for i in LABEL_MAP[a]).rstrip('\n')

def main():  # главный алгоритм программы, надо разобрать на процедуры и функции, абстрагировать хардкод
    # пути входных/выходных файлов. вот это всё в аргументы программы перенесу
    json_path = "jianheat.json"
    stat_path = expanduser("~")+"/.keystat.csv"
    heatmap_path = "jianheatmap.json"

    # чтение входных файлов
    keystat = read_keystat(stat_path)
    layout = read_layout(json_path)

    # это нужно для генерации цветов
    #minval = keystat.cnt.max()
    #maxval = 0
    minval = keystat.cnt.min()
    maxval = keystat.cnt.max()
    #gradient_colors = [(0xcc, 0xcc, 0xcc), (0xFF,0xFF,0x00), (0xdd,0x11,0x26)]
    #gradient_colors = [(0x00, 0x00, 0xFF), (0x00,0xFF,0x00), (0xFF,0x00,0x00)]
    gradient_colors = [(0x00, 0xba, 0xb4), (0xFF,0xD1,0x00), (0xcb, 0x2f, 0x2a)]
    #gradient_colors = [(0xFF, 0xFF, 0xFF), (0x60,0x60,0x60), (0x40, 0x40, 0x40)]

    a = 4 # дефолтное выравнивание легенд 4
    # счетчики для подсчёта количества обращений к клавишам на фирмварных слоях. У меня 4 модификатора, значит и счечика 4
    r_raise_cnt = 0
    l_raise_cnt = 0
    r_lower_cnt = 0
    l_lower_cnt = 0

    #count_keys = 0 # счетчик количества клавиш, ненужен. Использую для эксперементов
    for i, line in enumerate(layout): # проход во json'у
      if isinstance(line, list):
        for j, p in enumerate(line):
          if isinstance(p, dict): # если хешмапка с параметрами, то
            a = p.get('a', a) # попытаться получить выравнивание, иначе предыдущее
          elif isinstance(p, str):
            # count_keys += 1
            cnt = 0 # счетчик общего количества нажатий на клавишу (на клавише несколько легенд)
            d_p = decomp_label(a, p)
            hand = d_p[9] # тут хранится отметка на клавише какой рукой она нажимется, нужно для выбора счетчиков фирмварных модификаторов
            hold = d_p[7] # тут хранится действие при нажатие клавиши, там может быть имя фирмварного модфификатора

            for idx, k in enumerate(d_p[:-3]): # для всех легенд, кроме фронтальных
              if k: # если легенда есть
                for s_k in k.split(" "): # поделить её по пробелу и пройтись по составляющим, т.к. пробелом делятся разные действия с шифтом и без шифта, например: ". ,"
                  s_k = s_k.upper() # в верхний регистр всё такой у меня формат

                  s = keystat[(keystat.symbol == s_k)] # ищем в статистике символ совпадающий
                  if s.values.size == 0: # если не нашли, то
                    if idx in [3, 4, 5]: # если текущая легенда находится в центральной строке на клавише, то
                      s = keystat[(keystat.repr == s_k) & (keystat.iso_next_group == 1)] # поиск repr со включенным русским языком (надо чтобы не путать английские знаки препинания и русские
                    elif idx in [0, 1, 2]: # иначе если легенда в верхней строке
                      s = keystat[(keystat.repr == s_k) & (keystat.iso_next_group == 0)] # ищем репр с латинским языком

                  if s.values.size > 0: # если нашлись совпадения
                    cnt += s.cnt.values.sum() # в счетчик добавим колво нажатий по этим совпадениям

                  if idx in [0, 3, 6] and hand == 'r': # если легенда в левом столбце (значит она на lower слое) и рука правая
                    l_lower_cnt += cnt # увеличить счетчик левого lower количеством нажатий этой клавиши
                  elif idx in [2, 5, 8] and hand == 'r': # правый столбец, правая рука
                    l_raise_cnt += cnt # добавить к счетчику левого raise
                  elif idx in [2, 5, 8] and hand == 'l': # и так далее
                    r_raise_cnt += cnt
                  elif idx in [0, 3, 6] and hand == 'l':
                    r_lower_cnt += cnt

            # если легенда на клавише это легенда фирмварного слоя, то сохранить координаты клавиши и выравнивание легенды
            if hold.upper() == "RAISE" and hand == 'l':
              l_raise_i, l_raise_j, l_raise_a = i, j, a
            elif hold.upper() == "RAISE" and hand == 'r':
              r_raise_i, r_raise_j, r_raise_a = i, j, a
            elif hold.upper() == "LOWER" and hand == 'l':
              l_lower_i, l_lower_j, l_lower_a = i, j, a
            elif hold.upper() == "LOWER" and hand == 'r':
              r_lower_i, r_lower_j, r_lower_a = i, j, a

            c = list_get(d_p, 10, 0) # получить значение фронтальной центральной легенды, там должен быть счётчик нажатий клавиши
            c = 0 if c is '' else int(c) # инициализировать нулём или привести от строки к инту
            d_p[10] = cnt + c # добавить что насчитали
            layout[i][j] = comp_label(a, d_p) # записать обратно
    # этот участок кода падает, если не было найдено RAISE и LOWER
    #получить легенды правого raise, получить его счетчик, дописать колво нажатий которое было произведено через него и сохранить
    d_p = decomp_label(r_raise_a, layout[r_raise_i][r_raise_j])
    c = list_get(d_p, 10, 0)
    c = 0 if c is '' else int(c)
    d_p[10] = r_raise_cnt + c
    layout[r_raise_i][r_raise_j] = comp_label(r_raise_a, d_p)
    # и так далее
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

#   это алгоритм поиска минимальног и максимального счетчиков, но он не используется пока что, т.к. цвета выходят не очень. Но надо его юзать по хорошему, потом к нему перейдем
#    a = 4
#    for i, line in enumerate(layout):
#      if isinstance(line, list):
#        for j, p in enumerate(line):
#          if isinstance(p, dict):
#            a = p.get('a', a)
#          elif isinstance(p, str):
#            d_p = decomp_label(a, p)
#            c = list_get(d_p, 10, 0)
#            c = 0 if c is '' else int(c)
#            minval = min(c, minval)
#            maxval = max(c, maxval)

    # проходим по всеё раскладке как обычно с целью перед легендой клавиши вставить {c: #%%%%%%} с цветом легенды
    a = 4
    inserted = False # костыль помоему. Флаг который хранит то, что мы что то вставили на текущий индекс
    #cntr = 0
    for i, line in enumerate(layout):
      if isinstance(line, list):
        for j, p in enumerate(line):
          if inserted: # если вставили, то выключить флаг и скипнуть индекс
              inserted = False
              continue
          if isinstance(p, dict):
            a = p.get('a', a)
          elif isinstance(p, str):
            d_p = decomp_label(a, p)
            c = list_get(d_p, 10, 0)
            c = 0 if c is '' else int(c)
            col = format_rgb(val2rgb_gradient(minval, maxval, c, gradient_colors)) # посчитать цвет
            #norm_c = constrain(0, 1, cntr/count_keys) # эксперементы с альтернативной функцией для градиентов
            #col = format_rgb(astro_intensity(0,5,1,0.2,norm_c))
            layout[i].insert(j, {"c": col}) # вставить
            inserted = True # записать что вставили
            #cntr += 1 # подсчет номера текущей клавиши. Нужен для вывода цвета просто по палитре для эксперементов

    write_heatmap(layout, heatmap_path) # сохранить результат

if __name__ == "__main__":
    main()
