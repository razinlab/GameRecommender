import sqlite3
from better_profanity import profanity

conn = sqlite3.connect('../data/GameData.db')
cursor = conn.cursor()

cursor.execute('SELECT game_id, name FROM GameData')
games = cursor.fetchall()

for game_id, name in games:
    if profanity.contains_profanity(name):
        cursor.execute('DELETE FROM GameData WHERE game_id=?', (game_id,))

conn.commit()
conn.close()
