#!/usr/bin/python
# -*-coding:utf-8-*-
import sys
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


def try_int(arg, *args):
    args_len = len(args)
    if args_len == 0:
        x = arg
        default = 0
    else:
        default = arg
        x = args[0]
        args = args[1:]

    if 0 <= args_len <= 1 and isinstance(x, int):
        result = x
    else:
        try:
            result = int(str(x), *args)
        except (ValueError) as e:
            result = default

    return result


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

