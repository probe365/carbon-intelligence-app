import sqlite3
import uuid
import os
import shutil
from datetime import datetime, timedelta

# Choose a persistent path for SQLite when available (e.g., on Render with a mounted disk)
_env_db_path = os.getenv("DB_PATH")
if _env_db_path:
    DB_NAME = _env_db_path
else:
    # Default to a file alongside this module for local dev
    DB_NAME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trials.db")

# Ensure the directory for the DB exists (no-op if already present)
_db_dir = os.path.dirname(DB_NAME)
if _db_dir and not os.path.exists(_db_dir):
    try:
        os.makedirs(_db_dir, exist_ok=True)
    except PermissionError as e:
        # On platforms like Render, the mount path (e.g. /var/data) must be supplied
        # via a persistent disk. If the disk is not actually mounted yet (or on
        # free tier before adding the disk) attempting to create the top-level
        # directory can raise PermissionError. We log a clear hint instead of
        # crashing so the service can still start (it will later fail when the
        # DB is accessed if the path truly is unwritable).
        print(f"[DB] PermissionError creating '{_db_dir}': {e}. If deploying, attach a disk mounted at {_db_dir} or adjust DB_PATH.")
    except Exception as e:
        print(f"[DB] Unexpected error creating '{_db_dir}': {e}")

# Preflight writable check: give a clear error early if directory is not writable.
try:
    _parent = os.path.dirname(DB_NAME) or "."
    if _parent and os.path.isdir(_parent):
        test_file = os.path.join(_parent, ".__db_write_test__")
        with open(test_file, "w") as f:
            f.write("ok")
        os.remove(test_file)
    else:
        # Attempt to create if it doesn't exist (may fail and be caught below)
        os.makedirs(_parent, exist_ok=True)
except PermissionError as e:
    # Allow a graceful fallback when running on a free tier without disk support.
    if os.getenv("ALLOW_DB_FALLBACK", "1").lower() in ("1", "true", "yes"): 
        fallback = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trials.db")
        print(
            f"[DB][WARN] Cannot write to configured DB_PATH '{DB_NAME}' ({e}). "
            f"Falling back to non-persistent local file '{fallback}'. Upgrade and add a disk to persist data."
        )
        DB_NAME = fallback
        _db_dir = os.path.dirname(DB_NAME)
    else:
        msg = (
            f"[DB][FATAL] Directory not writable for DB_PATH='{DB_NAME}'. Attach a Render Disk mounted at '{_parent}' "
            f"(Render UI: Service -> Disks -> Add Disk, Mount Path '{_parent}', then redeploy) or change DB_PATH. Error: {e}"
        )
        print(msg)
        raise SystemExit(1)
except Exception as e:
    print(f"[DB] Warning during writable preflight: {e}")


def _migrate_bundled_db_if_needed():
    """Copy a bundled trials.db to the persistent DB path on first boot.

    This allows keeping existing local/demo data when switching to a mounted disk
    (e.g., Render). Only runs if DB_PATH points elsewhere, the target doesn't
    exist yet, and a bundled file is present.
    """
    try:
        bundled = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trials.db")
        target = os.path.abspath(DB_NAME)
        if os.path.abspath(bundled) != target and (not os.path.exists(target)) and os.path.exists(bundled):
            shutil.copy2(bundled, target)
            print(f"[DB] Seeded persistent DB from bundled file -> {target}")
    except Exception as e:
        print(f"[DB] Migration warning: {e}")

def init_db():
    # One-time migration before opening the database
    _migrate_bundled_db_if_needed()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            full_name TEXT,
            company TEXT,
            role TEXT,
            country TEXT,
            registration_date TEXT
        )
    """)
    conn.commit()
    conn.close()




def upgrade_db():
    # No upgrade needed for users-only schema
    pass

def save_user_to_db(user_data):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO users (
                email, full_name, company, role, country, registration_date
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            user_data["email"],
            user_data["full_name"],
            user_data["company"],
            user_data["role"],
            user_data["country"],
            user_data["registration_date"]
        ))
        conn.commit()
    except Exception as e:
        print(f"Erro ao salvar usuário: {e}")
        raise
    finally:
        conn.close()


def get_all_users():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT email, full_name, company, role, country, registration_date
        FROM users
        ORDER BY registration_date DESC
    """)
    rows = cursor.fetchall()
    conn.close()

    users = []
    for row in rows:
        users.append({
            "email": row[0],
            "full_name": row[1],
            "company": row[2],
            "role": row[3],
            "country": row[4],
            "registration_date": row[5]
        })
    return users

