import pg8000.native
import sys
import os
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    try:
        return pg8000.native.Connection(
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            host="localhost",
            port=5432,
            database=os.getenv("POSTGRES_DB")
        )
    except Exception as e:
        print(f"[DB HIBA] {e}", file=sys.stderr)
        return None