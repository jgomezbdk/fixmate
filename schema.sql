PRAGMA foreign_keys = ON;

CREATE TABLE users (
  id       INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT    NOT NULL UNIQUE,
  password TEXT    NOT NULL
);

CREATE TABLE tasks (
  id             INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id        INTEGER NOT NULL,
  title          TEXT    NOT NULL,
  category       TEXT,
  due_date       TEXT,
  frequency      TEXT,
  cost           REAL,
  estimated_time TEXT,
  guide          TEXT,
  video_url      TEXT,
  completed      INTEGER NOT NULL DEFAULT 0,
  FOREIGN KEY(user_id) REFERENCES users(id)
);
