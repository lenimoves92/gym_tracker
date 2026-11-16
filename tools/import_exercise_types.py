"""Rebuild exercise_types.json from the Excel exercise matrix.

Usage (dev only, needs `pip install openpyxl`):
    python tools/import_exercise_types.py uebungsmatrix_gym-tracker.xlsx

Matrix layout: header row with "Übung" in column A, one column per workout type,
an "x" marks the assignment. Columns are recognised by their header word, not by the
"(Q)"-style suffix, because Excel autocorrects "(R)" to "®" and "(E)" to "€".
"""
import json
import sys
from pathlib import Path

import openpyxl

OUT = Path(__file__).resolve().parent.parent / 'exercise_types.json'
TYPES = {'Q': 'Quick', 'R': 'Regular', 'E': 'Extended', 'B': 'Bonus'}


def main(xlsx_path):
    ws = openpyxl.load_workbook(xlsx_path, data_only=True).active

    # Locate the header row and map each type column by its header word
    header_row, columns = None, {}
    for row in ws.iter_rows():
        if row[0].value and str(row[0].value).strip().lower().endswith('bung'):  # "Übung"
            header_row = row[0].row
            for cell in row[1:]:
                for code, word in TYPES.items():
                    if cell.value and word.lower() in str(cell.value).lower():
                        columns[code] = cell.column - 1
            break
    if header_row is None or set(columns) != set(TYPES):
        sys.exit(f"Header row / type columns not found (found: {columns})")

    exercises, problems = {}, []
    for row in ws.iter_rows(min_row=header_row + 1, values_only=True):
        name = str(row[0]).strip() if row[0] else ''
        if not name or name.startswith('Anzahl'):  # skip blanks and the totals row
            continue
        marks = [code for code, col in columns.items()
                 if row[col] and str(row[col]).strip().lower() == 'x']
        if name in exercises:
            problems.append(f"duplicate row: {name}")
        elif len(marks) != 1:
            problems.append(f"{name}: {len(marks)} assignments {marks}")
        else:
            exercises[name] = marks[0]

    data = {'types': TYPES, 'exercises': dict(sorted(exercises.items(), key=lambda kv: kv[0].lower()))}
    OUT.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f"Wrote {len(exercises)} exercises to {OUT.name}")
    for p in problems:
        print("SKIPPED:", p)


if __name__ == '__main__':
    main(sys.argv[1])
