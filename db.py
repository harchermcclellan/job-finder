import os
import json
import hashlib
import psycopg2
from datetime import datetime, timedelta, timezone

DATABASE_URL=os.getenv("DATABASE_URL")


def get_conn():
    print(DATABASE_URL)
    try:
        return psycopg2.connect(DATABASE_URL, sslmode="require")
    except Exception as e:
        print(e)
        print(DATABASE_URL)
        return
        
def make_key(description: str, location: str, work_type: str, salary: str) -> str:
    raw = f"{description}|{location}|{work_type}|{salary}".lower().strip()
    return hashlib.sha256(raw.encode()).hexdigest()

def get_cached(cache_key: str) -> list | None:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT results FROM search_cache
            WHERE cache_key = %s AND created_at > %s
        """, (cache_key, cutoff))
        row = cur.fetchone()
    return row[0] if row else None

def set_cached(cache_key: str, role: str, location: str, results: list):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            INSERT INTO search_cache (cache_key, role, location, results, created_at)
            VALUES (%s, %s, %s, %s, NOW())
            ON CONFLICT (cache_key) DO UPDATE
                SET results = EXCLUDED.results,
                    created_at = NOW()
        """, (cache_key, role, location, json.dumps(results)))