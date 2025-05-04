import sqlite3

def seed():
    conn = sqlite3.connect('fixmate.db')
    cur = conn.cursor()
    # Demo user: demo/demo
    cur.execute("INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)",
                ("demo", "demo"))
    conn.commit()
    conn.close()
    print("✔ Seeded demo user: demo/demo")

if __name__ == '__main__':
    seed()
