#!/usr/bin/python
# -*- coding: utf-8 -*-

from qtextasdata import QTextAsData,QInputParams
from os.path import expanduser
import csv
import argparse


def read_keylog(path, sep='\t'):
    q = QTextAsData()
    q.load_data(path, QInputParams(delimiter=sep, skip_header=True, input_encoding="utf-8"))
    return q


def calc_press_stat(q, keylog_path):
    return q.execute('''
      SELECT COUNT(pressed) AS cnt,
             symbol,
             repr,
             (mods_mask >> 13) & 1 AS iso_next_group
      FROM {file_path}
      WHERE (pressed = 1)
        AND (repeated = 0)
      GROUP BY symbol, repr, iso_next_group
      ORDER BY cnt DESC'''.format(file_path=keylog_path))


def write_stat(stat, path, sep='\t'):
    with open(path, 'w') as stat_file:
        writer = csv.writer(stat_file, delimiter=sep)
        writer.writerow(stat.metadata.output_column_name_list)
        [writer.writerow(line) for line in stat.data]


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


def main():
    keylog_path, stat_path = parse_args()
    q = read_keylog(keylog_path)
    write_stat(calc_press_stat(q, keylog_path), stat_path)


if __name__ == "__main__":
    main()
