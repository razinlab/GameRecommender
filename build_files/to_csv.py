import pandas as pd
import numpy as np
import sqlite3

conn = sqlite3.connect('../data/GameData.db')
csv = pd.read_sql_query("SELECT * FROM GameData", conn)
csv.to_csv('GameData.csv', index=False)
