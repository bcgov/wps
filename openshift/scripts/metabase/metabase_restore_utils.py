#!/usr/bin/env python3
import re
import sys
from pathlib import Path


def extract_table(backup_file, table_name):
    with open(Path(backup_file).resolve()) as f:
        content = f.read()
    pattern = rf'(COPY public\.{table_name} \(([^)]+)\) FROM stdin;\n)(.*?)\n\\.'
    m = re.search(pattern, content, re.DOTALL)
    if not m:
        print(f"WARNING: table {table_name!r} not found in backup", file=sys.stderr)
        return None, [], []
    header = m.group(1).rstrip("\n")
    cols = [c.strip().strip('"') for c in m.group(2).split(",")]
    rows = [line for line in m.group(3).split("\n") if line]
    return header, cols, rows


def filter_by(rows, cols, col_name, ids):
    idx = cols.index(col_name)
    return [r.split("\t") for r in rows if r.split("\t")[idx] in {str(i) for i in ids}]


def get_val(parts, cols, col_name):
    return parts[cols.index(col_name)] if col_name in cols else None


def set_val(parts, cols, col_name, val):
    if col_name in cols:
        parts[cols.index(col_name)] = val
    return parts


def append_copy_block(out, header, rows, label):
    out.append(f"-- {label}")
    out.append(header)
    out += ["\t".join(p) for p in rows]
    out += ["\\.", ""]


def write_sql(out, output_path):
    with open(Path(output_path).resolve(), "w") as f:
        f.write("\n".join(out))
