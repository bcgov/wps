#!/usr/bin/env python3
"""
Restore specific Metabase users from a pg_dump backup.
Usage: python3 metabase_user_restore_extract.py <backup.sql> <id1> [id2 ...] [--output FILE] [--reset-password]
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
    parser = argparse.ArgumentParser(description="Restore Metabase users from backup")
    parser.add_argument("backup", help="Path to the decompressed backup SQL file")
    parser.add_argument("user_ids", nargs="+", help="User IDs to restore")
    parser.add_argument("--output", default="metabase_user_restore.sql", help="Output file")
    parser.add_argument("--reset-password", action="store_true",
                        help="Clear password hash so user must set a new password on next login")
    args = parser.parse_args()

    user_ids = set(args.user_ids)
    out = ["BEGIN;", ""]

    # core_user
    header, cols, rows = extract_table(args.backup, "core_user")
    if not header:
        print("ERROR: core_user table not found in backup", file=sys.stderr)
        sys.exit(1)

    users = filter_by(rows, cols, "id", user_ids)
    if not users:
        print(f"ERROR: no users found with IDs {user_ids}", file=sys.stderr)
        sys.exit(1)

    for p in users:
        # Ensure user is active
        set_val(p, cols, "is_active", "t")
        if args.reset_password:
            set_val(p, cols, "password", "\\N")
            set_val(p, cols, "password_salt", "\\N")
            set_val(p, cols, "reset_token", "\\N")
            set_val(p, cols, "reset_triggered", "\\N")

    emails = ", ".join(get_val(p, cols, "email") for p in users)
    out.append(f"-- {len(users)} users: {emails}")
    out.append(header)
    out += ["\t".join(p) for p in users]
    out += ["\\.", ""]

    # permissions_group_membership
    header, cols, rows = extract_table(args.backup, "permissions_group_membership")
    if header:
        memberships = filter_by(rows, cols, "user_id", user_ids)
        out.append(f"-- {len(memberships)} group memberships")
        out.append(header)
        out += ["\t".join(p) for p in memberships]
        out += ["\\.", ""]

    # Sequence reset
    out += [
        "-- Reset sequence",
        "SELECT setval('core_user_id_seq', (SELECT MAX(id) FROM core_user));",
        "SELECT setval('permissions_group_membership_id_seq', (SELECT MAX(id) FROM permissions_group_membership));",
        "",
        "COMMIT;",
    ]

    with open(Path(args.output).resolve(), "w") as f:
        f.write("\n".join(out))

    print(f"Written to {args.output}")
    print(f"  {len(users)} users, {len(memberships) if header else 0} group memberships")
    if args.reset_password:
        print("  Password cleared — users will need to set a new password via 'Forgot password'")


if __name__ == "__main__":
    main()
