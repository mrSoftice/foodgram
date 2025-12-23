import csv
import json
from pathlib import Path


def read_json(path: Path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def read_csv(path: Path):
    with open(path, 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def read_data_from_file(filename):
    if Path(filename).suffix.lower() == '.csv':
        rows_from_file = read_csv(filename)
    else:
        rows_from_file = read_json(filename)
    return rows_from_file
