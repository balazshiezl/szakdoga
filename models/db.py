# models/db.py

import pg8000.native
import sys

def get_connection():
    try:
        return pg8000.native.Connection(
            user="hbalazs",
            password="krokodil1",
            host="localhost",
            port=5432,
            database="szakdolgozat"
        )
    except Exception as e:
        print(f"[DB HIBA] {e}", file=sys.stderr)
        return None
