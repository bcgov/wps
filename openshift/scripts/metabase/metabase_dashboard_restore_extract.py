#!/usr/bin/env python3
"""
Restore specific Metabase dashboards from a pg_dump backup.
Usage: python3 extract_restore.py <backup.sql> <id1> [id2 ...] [--owner USER_ID] [--output FILE]
"""
import argparse
import sys

from metabase_restore_utils import append_copy_block, extract_table, filter_by, get_val, set_val, write_sql


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
    append_copy_block(out, header, dashboards, f"{len(dashboards)} dashboards: {names}")

    # Dashboard tabs
    header, cols, rows = extract_table(args.backup, "dashboard_tab")
    if header:
        tabs = filter_by(rows, cols, "dashboard_id", dashboard_ids)
        append_copy_block(out, header, tabs, f"{len(tabs)} dashboard tabs")

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
    append_copy_block(out, header, cards, f"{len(cards)} cards")
    append_copy_block(out, dc_header, dashboardcards, f"{len(dashboardcards)} dashboardcards")

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

    write_sql(out, args.output)
    print(f"Written to {args.output}")
    print(f"  {len(dashboards)} dashboards, {len(cards)} cards, {len(dashboardcards)} dashboardcards")


if __name__ == "__main__":
    main()
