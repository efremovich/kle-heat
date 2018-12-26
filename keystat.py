#!/usr/bin/python
# -*- coding: utf-8 -*-

from os.path import expanduser
from re import sub
import pandas as pd
import argparse


def read_keylog(path, sep='\t'):
    return pd.read_csv(path, delimiter=sep, header=0)


def calc_press_stat(keylog):  # optimize
    keylog["iso_next_group"] = keylog["mods_mask"].map(
        lambda x: (x >> 13) & 1)
    data = keylog[(keylog["pressed"] == 1) &
                  (keylog["repeated"] == 0)] \
        .groupby(["symbol", "iso_next_group"]) \
        .size() \
        .sort_values(ascending=False)
    data = pd.DataFrame({"sm_m": data.index, "cnt": data.values})
    data[["symbol", "iso_next_group"]] = data["sm_m"].apply(pd.Series)
    data = data.drop(columns="sm_m")
    data = pd.merge(data, keylog[["symbol", "repr"]],
                    on="symbol", how="left").drop_duplicates()
    data.fillna(value="None", inplace=True)
    return data


def write_stat(stat, path, sep='\t'):
    stat.to_csv(path, sep=sep, encoding="utf-8", index=False)


def parse_args():
    parser = argparse.ArgumentParser(
        description='Statistics aggregator for inputlistener.py')
    parser.add_argument('-i', action='store', dest='keylog_path',
                        help='keylog csv file path; default ~/.keylog.csv',
                        default=expanduser("~") + "/.keylog.csv")
    parser.add_argument(
        '-o',
        action='store',
        dest='stat_path',
        help='statistics csv file path; default ~/.keystat.csv',
        default=expanduser("~") +
        "/.keystat.csv")
    args = parser.parse_args()
    return args.keylog_path, args.stat_path

#def main():
keylog_path, stat_path = parse_args()
keylog = read_keylog(keylog_path)
keylog.symbol = keylog.symbol.map(lambda x: x.upper())
keylog.repr = keylog.repr.map(
    lambda x: (
        lambda y: repr(
            y.upper()) if isinstance(y, str) else y)(eval(x)))
write_stat(calc_press_stat(keylog), stat_path)


#if __name__ == "__main__":
#    main()
