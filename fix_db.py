"""
fix_db.py

Safe DB inspector & fixer for the 'detections' table used by your Flask app.

What it does:
- makes a timestamped backup of database.db
- prints current tables and 'detections' schema + sample rows
- if 'location' and 'incharge' are missing (and no other schema mismatch), it will ALTER TABLE to add them
- otherwise it will perform a safe migration:
    create new table with the desired schema, copy data mapping existing cols -> desired cols,
    rename old table to detections_old_<ts>, rename new table to detections
- prints final schema & sample rows for verification
"""

import sqlite3
import os
import shutil
from datetime import datetime

DB = "database.db"
DESIRED_COLS = ["id", "filename", "detected_classes", "timestamp", "location", "incharge"]

def backup_db(db_path: str) -> str:
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database file not found: {db_path}")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"database_backup_{ts}.db"
    shutil.copyfile(db_path, backup_name)
    return backup_name

def get_tables(conn):
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    return [r[0] for r in cur.fetchall()]

def get_table_info(conn, table):
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table});")
    return cur.fetchall()  # rows: (cid, name, type, notnull, dflt_value, pk)

def show_sample_rows(conn, table, limit=5):
    cur = conn.cursor()
    try:
        cur.execute(f"SELECT * FROM {table} LIMIT {limit}")
        rows = cur.fetchall()
        return rows
    except Exception as e:
        return f"Could not read rows from {table}: {e}"

def add_missing_columns(conn, table, missing_cols):
    cur = conn.cursor()
    for col in missing_cols:
        print(f"Adding column: {col} TEXT")
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {col} TEXT")
    conn.commit()

def migrate_table(conn, old_table, desired_cols):
    cur = conn.cursor()
    new_table = f"{old_table}_new"
    # Create new table
    create_sql = f"""
    CREATE TABLE IF NOT EXISTS {new_table} (
        id TEXT PRIMARY KEY,
        filename TEXT,
        detected_classes TEXT,
        timestamp TEXT,
        location TEXT,
        incharge TEXT
    )
    """
    print("Creating new table with desired schema:", new_table)
    cur.execute(create_sql)

    # existing columns in old table
    cur.execute(f"PRAGMA table_info({old_table})")
    existing_cols = [r[1] for r in cur.fetchall()]
    print("Existing columns in old table:", existing_cols)

    # build select list mapping existing -> desired, else NULL
    select_parts = []
    for col in desired_cols:
        if col in existing_cols:
            select_parts.append(col)
        else:
            select_parts.append(f"NULL AS {col}")

    select_sql = ", ".join(select_parts)
    insert_sql = f"INSERT INTO {new_table} ({', '.join(desired_cols)}) SELECT {select_sql} FROM {old_table};"

    print("Copying data from old to new table...")
    cur.execute("BEGIN")
    try:
        cur.execute(insert_sql)
        # rename old table to keep as backup
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        old_backup_name = f"{old_table}_old_{ts}"
        cur.execute(f"ALTER TABLE {old_table} RENAME TO {old_backup_name}")
        cur.execute(f"ALTER TABLE {new_table} RENAME TO {old_table}")
        conn.commit()
        print(f"Migration succeeded. Old table renamed to: {old_backup_name}")
    except Exception as e:
        conn.rollback()
        raise

def main():
    if not os.path.exists(DB):
        print(f"Database file '{DB}' not found in current folder ({os.getcwd()}). Exiting.")
        return

    print("1) Creating backup of database...")
    backup_name = backup_db(DB)
    print("Backup created:", backup_name)

    conn = sqlite3.connect(DB)
    try:
        print("\n2) Current tables:")
        tables = get_tables(conn)
        print(tables)

        if "detections" not in tables:
            print("\nNo 'detections' table found. Creating a new one with desired schema.")
            cur = conn.cursor()
            cur.execute("""
            CREATE TABLE IF NOT EXISTS detections (
                id TEXT PRIMARY KEY,
                filename TEXT,
                detected_classes TEXT,
                timestamp TEXT,
                location TEXT,
                incharge TEXT
            )
            """)
            conn.commit()
            print("Table 'detections' created.")
            print("\nFinal schema:")
            print(get_table_info(conn, "detections"))
            return

        print("\n3) Current 'detections' schema (PRAGMA table_info):")
        info = get_table_info(conn, "detections")
        for row in info:
            print(row)
        existing_cols = [r[1] for r in info]

        print("\n4) Sample rows (up to 5):")
        print(show_sample_rows(conn, "detections", limit=5))

        # Decide action
        missing = [c for c in DESIRED_COLS if c not in existing_cols]
        extra = [c for c in existing_cols if c not in DESIRED_COLS]

        print("\nMissing desired columns:", missing)
        print("Extra columns present:", extra)

        if missing and not extra:
            # safe: just add missing columns
            print("\nOnly desired columns are missing. Adding missing columns...")
            add_missing_columns(conn, "detections", missing)
            print("Columns added.")
        elif not missing and not extra:
            print("\nSchema already matches desired schema. No action needed.")
        else:
            # complex case — do migration
            print("\nSchema differs (missing or extra columns). Performing safe migration...")
            migrate_table(conn, "detections", DESIRED_COLS)
            print("Migration finished.")

        print("\n5) Final 'detections' schema:")
        info_after = get_table_info(conn, "detections")
        for row in info_after:
            print(row)

        print("\n6) Sample rows after changes (up to 5):")
        print(show_sample_rows(conn, "detections", limit=5))
    finally:
        conn.close()
    print("\nAll done. If something looks wrong, you can restore the backup:")
    print(f"  To restore: replace {DB} with the backup file, e.g. copy {backup_name} {DB}")

if __name__ == "__main__":
    main()
