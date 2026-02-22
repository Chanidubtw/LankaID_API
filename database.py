import sqlite3
import os

DB_PATH = os.getenv("DB_PATH", "lanka_nic.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            plan TEXT DEFAULT 'free',
            request_count INTEGER DEFAULT 0,
            monthly_limit INTEGER DEFAULT 200,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_used TIMESTAMP,
            is_active INTEGER DEFAULT 1
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS request_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            api_key TEXT NOT NULL,
            endpoint TEXT NOT NULL,
            nic_input TEXT,
            success INTEGER,
            error_message TEXT,
            ip_address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    print("✅ Database initialized.")


def get_api_key_record(key: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM api_keys WHERE key = ? AND is_active = 1", (key,))
    row = cursor.fetchone()
    conn.close()
    return row


def increment_request_count(key: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE api_keys 
        SET request_count = request_count + 1, last_used = CURRENT_TIMESTAMP 
        WHERE key = ?
    """, (key,))
    conn.commit()
    conn.close()


def log_request(api_key: str, endpoint: str, nic_input: str, success: bool, error: str, ip: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO request_logs (api_key, endpoint, nic_input, success, error_message, ip_address)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (api_key, endpoint, nic_input, 1 if success else 0, error, ip))
    conn.commit()
    conn.close()


def create_api_key_record(key: str, name: str, email: str, plan: str = "free", limit: int = 200):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO api_keys (key, name, email, plan, monthly_limit)
            VALUES (?, ?, ?, ?, ?)
        """, (key, name, email, plan, limit))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()
