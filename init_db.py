# init_db.py
import sqlite3

DB = 'fixmate.db'
SCHEMA = 'schema.sql'

def init_db():
    with open(SCHEMA, 'r') as f:
        sql = f.read()
    conn = sqlite3.connect(DB)
    conn.executescript(sql)
    conn.close()
    print(f"Initialized {DB} from {SCHEMA}")

if __name__ == '__main__':
    init_db()
