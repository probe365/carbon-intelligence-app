import sqlite3
import uuid
import os
import shutil
from datetime import datetime

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
    os.makedirs(_db_dir, exist_ok=True)


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
        CREATE TABLE IF NOT EXISTS trials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            trial_key TEXT UNIQUE NOT NULL,
            full_name TEXT,
            company TEXT,
            role TEXT,
            country TEXT,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            queries_used INTEGER DEFAULT 0,
            queries_limit INTEGER DEFAULT 100,
            registration_date TEXT,
            status TEXT DEFAULT 'active'
        )
    """)
    conn.commit()
    conn.close()




def upgrade_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Verifica colunas da tabela trials
    cursor.execute("PRAGMA table_info(trials)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'last_access' not in columns:
        cursor.execute("ALTER TABLE trials ADD COLUMN last_access TEXT")

    # Verifica se a tabela access_logs existe
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='access_logs'
    """)
    table_exists = cursor.fetchone()
    if not table_exists:
        cursor.execute("""
            CREATE TABLE access_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trial_key TEXT NOT NULL,
                query TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                ip_address TEXT,
                FOREIGN KEY(trial_key) REFERENCES trials(trial_key)
            )
        """)

    conn.commit()
    conn.close()


def trial_exists(email):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM trials WHERE email = ?", (email,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists

def save_trial_to_db(trial_data):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO trials (
                email, trial_key, full_name, company, role, country,
                start_date, end_date, queries_used, queries_limit,
                registration_date, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            trial_data["email"],
            trial_data["trial_key"],
            trial_data["full_name"],
            trial_data["company"],
            trial_data["role"],
            trial_data["country"],
            trial_data["start_date"],
            trial_data["end_date"],
            trial_data["queries_used"],
            trial_data["queries_limit"],
            trial_data["registration_date"],
            trial_data["status"]
        ))
        conn.commit()
    except Exception as e:
        print(f"Erro ao salvar trial: {e}")
        raise
    finally:
        conn.close()


def get_trial_by_key(trial_key):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT email, trial_key, queries_used, queries_limit, end_date
        FROM trials
        WHERE trial_key = ?
    """, (trial_key,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "email": row[0],
            "trial_key": row[1],
            "queries_used": row[2],
            "queries_limit": row[3],
            "end_date": row[4]
        }
    return None

def count_trials(status=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    if status:
        cursor.execute("SELECT COUNT(*) FROM trials WHERE status = ?", (status,))
    else:
        cursor.execute("SELECT COUNT(*) FROM trials")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def increment_queries_used(trial_key):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        UPDATE trials
        SET queries_used = queries_used + 1,
            last_access = ?
        WHERE trial_key = ?
    """, (now, trial_key))
    conn.commit()
    conn.close()


def get_all_trials():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT email, trial_key, full_name, company, role, country,
               queries_used, queries_limit, registration_date, status, last_access
        FROM trials
        ORDER BY registration_date DESC
    """)
    rows = cursor.fetchall()
    conn.close()

    trials = []
    for row in rows:
        trials.append({
            "email": row[0],
            "trial_key": row[1],
            "full_name": row[2],
            "company": row[3],
            "role": row[4],
            "country": row[5],
            "queries_used": row[6],
            "queries_limit": row[7],
            "registration_date": row[8],
            "status": row[9],
            "last_access": row[10]
        })
    return trials

def log_access(trial_key, query, ip_address=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO access_logs (trial_key, query, timestamp, ip_address)
        VALUES (?, ?, ?, ?)
    """, (trial_key, query, timestamp, ip_address))
    conn.commit()
    conn.close()

def update_expired_trials():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        """
        UPDATE trials
        SET status = 'expired'
        WHERE end_date < ? AND status = 'active'
        """,
        (now,),
    )
    affected = cursor.rowcount if hasattr(cursor, 'rowcount') else 0
    conn.commit()
    conn.close()
    return affected
