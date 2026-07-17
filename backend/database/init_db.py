import sqlite3
from backend.config import get_db_path, logger

def init_db():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.close()
    logger.info(f"Database initialized at {db_path}")
    return db_path