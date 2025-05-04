import sqlite3

def init_db():
    conn = sqlite3.connect('fixmate.db')
    with open('schema.sql', 'r') as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()
    print("✔ Initialized fixmate.db")

if __name__ == '__main__':
    init_db()
