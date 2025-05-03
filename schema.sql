-- schema.sql

-- Table: users
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
);

-- Table: tasks
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    category TEXT,
    due_date TEXT,
    frequency TEXT,
    cost REAL,
    is_completed INTEGER NOT NULL DEFAULT 0,
    guide TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
