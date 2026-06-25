#!/usr/bin/env python3
"""
Restore specific Metabase dashboards from a pg_dump backup.
Usage: python3 extract_restore.py <backup.sql> <id1> [id2 ...] [--owner USER_ID] [--output FILE]
"""
import argparse
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


def main():
    parser = argparse.ArgumentParser(description="Restore Metabase dashboards from backup")
    parser.add_argument("backup", help="Path to the decompressed backup SQL file")
    parser.add_argument("dashboard_ids", nargs="+", help="Dashboard IDs to restore")
    parser.add_argument("--owner", default="10", help="Metabase user ID to assign as creator (default: 10)")
    parser.add_argument("--output", default="metabase_restore.sql", help="Output file")
    args = parser.parse_args()

    dashboard_ids = set(args.dashboard_ids)
    new_owner = args.owner
    valid_users = {"1", "13371338", new_owner}

    out = ["BEGIN;", ""]

    # Dashboards
    header, cols, rows = extract_table(args.backup, "report_dashboard")
    dashboards = filter_by(rows, cols, "id", dashboard_ids)
    for p in dashboards:
        if get_val(p, cols, "creator_id") not in valid_users:
            set_val(p, cols, "creator_id", new_owner)
    names = ", ".join(get_val(p, cols, "name") for p in dashboards)
    out.append(f"-- {len(dashboards)} dashboards: {names}")
    out.append(header)
    out += ["\t".join(p) for p in dashboards]
    out += ["\\.", ""]

    # Dashboard tabs
    header, cols, rows = extract_table(args.backup, "dashboard_tab")
    if header:
        tabs = filter_by(rows, cols, "dashboard_id", dashboard_ids)
        out.append(f"-- {len(tabs)} dashboard tabs")
        out.append(header)
        out += ["\t".join(p) for p in tabs]
        out += ["\\.", ""]

    # Dashboardcards (discover card IDs dynamically)
    dc_header, dc_cols, dc_rows = extract_table(args.backup, "report_dashboardcard")
    dashboardcards = filter_by(dc_rows, dc_cols, "dashboard_id", dashboard_ids)
    card_ids = {
        get_val(p, dc_cols, "card_id")
        for p in dashboardcards
        if get_val(p, dc_cols, "card_id") != "\\N"
    }

    # Cards
    header, cols, rows = extract_table(args.backup, "report_card")
    cards = filter_by(rows, cols, "id", card_ids)
    for p in cards:
        if get_val(p, cols, "creator_id") not in valid_users:
            set_val(p, cols, "creator_id", new_owner)
        if "made_public_by_id" in cols and get_val(p, cols, "made_public_by_id") not in valid_users | {"\\N"}:
            set_val(p, cols, "made_public_by_id", "\\N")
    out.append(f"-- {len(cards)} cards")
    out.append(header)
    out += ["\t".join(p) for p in cards]
    out += ["\\.", ""]

    # Dashboardcards
    out.append(f"-- {len(dashboardcards)} dashboardcards")
    out.append(dc_header)
    out += ["\t".join(p) for p in dashboardcards]
    out += ["\\.", ""]

    # Sequence resets
    out += [
        "-- Reset sequences",
        "SELECT setval('report_dashboard_id_seq', (SELECT MAX(id) FROM report_dashboard));",
        "SELECT setval('dashboard_tab_id_seq', (SELECT MAX(id) FROM dashboard_tab));",
        "SELECT setval('report_card_id_seq', (SELECT MAX(id) FROM report_card));",
        "SELECT setval('report_dashboardcard_id_seq', (SELECT MAX(id) FROM report_dashboardcard));",
        "",
        "COMMIT;",
    ]

    with open(Path(args.output).resolve(), "w") as f:
        f.write("\n".join(out))

    print(f"Written to {args.output}")
    print(f"  {len(dashboards)} dashboards, {len(cards)} cards, {len(dashboardcards)} dashboardcards")


if __name__ == "__main__":
    main()
