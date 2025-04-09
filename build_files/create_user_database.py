import sqlite3


def create_database():
    conn = sqlite3.connect('../data/users.db')
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS saved_games (
        save_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        game_id TEXT NOT NULL,
        game_name TEXT NOT NULL,
        game_url TEXT,
        image_url TEXT,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
        UNIQUE(user_id, game_id)
    )
    """)

    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_user_games 
    ON saved_games(user_id)
    """)

    conn.commit()
    conn.close()
