# kle-heat
heatmaps for keyboard-layout-editor.com

Поставьте inputlistener.py на автозапуск

usage: inputlistener.py [-h] [-o KEYLOG_PATH]

Statistics aggregator for inputlistener.py

optional arguments:
  -h, --help      show this help message and exit
  -o KEYLOG_PATH  keylog csv file path; default ~/.keylog.csv


Как статистика набежит, запустите keystat.py, тоже есть хелпа и параметры поумолчанию

usage: keystat.py [-h] [-i KEYLOG_PATH] [-o STAT_PATH]

Statistics aggregator for inputlistener.py

optional arguments:
  -h, --help      show this help message and exit
  -i KEYLOG_PATH  keylog csv file path; default ~/.keylog.csv
  -o STAT_PATH    statistics csv file path; default ~/.keystat.csv


Затем запустите apply_stat2kle.py тут надо указать параметр 
-L /путь/до/раскладки/c/kle.json и 
-o /путь/до/файла/с/результатом. 

[efremov@Africa kle-heat]$ python ./apply_stat2kle.py -h
usage: apply_stat2kle.py [-h] [-i STAT_PATH] -l LAYOUT_PATH -o OUTPUT_PATH

Draws heatmap on keyboard-layout-editor json

optional arguments:
  -h, --help      show this help message and exit
  -i STAT_PATH    keystat csv file path; default ~/.keystat.csv
  -l LAYOUT_PATH  keyboard-layout-editor json path
  -o OUTPUT_PATH  result kle json path


Ну и результат можно загружать на kle

python ./keystat.py -i ~/Dev/keyStatData/.keylog.csv -o ~/Dev/keyStatData/.keystat.csv

python ./apply_stat2kle.py -i ~/Dev/keyStatData/.keystat.csv -l ~/Dev/keyStatData/cojian-ru.json -o ~/Dev/keyStatData/result.json


