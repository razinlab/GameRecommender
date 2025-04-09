import sqlite3
import requests
import time
import json


CLIENT_ID = "i9awwx6hs5352lbeovcmrdbbr8bdom"
CLIENT_SECRET = "knl05h8u6djdlqgj5vnjk9w9yiqecv"


def create_database():
    conn = sqlite3.connect('../data/GameData.db')
    cursor = conn.cursor()
    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS GameData (
            game_id INT PRIMARY KEY,
            name TEXT,
            summary TEXT,
            storyline TEXT,
            aggregated_rating REAL,
            genres TEXT,
            platforms TEXT,
            themes TEXT,
            dlcs TEXT,
            dlc_count INT,
            expansion_count INT,
            game_engines TEXT,
            involved_companies TEXT,
            keywords TEXT,
            similar_games TEXT,
            player_perspectives TEXT,
            cover_url TEXT,
            steam_url TEXT,
            gog_url TEXT,
            playstation_url TEXT,
            xbox_url TEXT,
            epic_url TEXT,
            nintendo_url TEXT,
            official_url TEXT,
            release_date INT,
            release_date_human TEXT
        )
        '''
    )
    conn.commit()
    conn.close()


def get_access_token():
    url = "https://id.twitch.tv/oauth2/token"
    credentials = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        "grant_type": "client_credentials"
    }
    response = requests.post(url, params=credentials)
    return response.json().get('access_token')


def insert_data(games):
    conn = sqlite3.connect('../data/GameData.db')
    cursor = conn.cursor()

    inserted_count = 0

    for game in games:
        dlc_count = len(game.get('dlcs', []))
        expansion_count = len(game.get('expansions', []))
        release_dates = game.get('release_dates', [])
        release_date = None
        release_date_human = None

        if release_dates:
            sorted_dates = sorted(release_dates, key=lambda d: d.get('date', float('inf')))
            release_date = sorted_dates[0].get('date')
            release_date_human = sorted_dates[0].get('human')

        game_engines = json.dumps([e['name'] for e in game.get('game_engines', []) if 'name' in e])
        involved_companies = json.dumps([c['company']['name'] for c in game.get('involved_companies', []) if
                                       'company' in c and 'name' in c['company']])
        keywords = json.dumps([k['name'] for k in game.get('keywords', []) if 'name' in k])
        similar_games = json.dumps([g['name'] for g in game.get('similar_games', []) if 'name' in g])
        genres_str = json.dumps([g['name'] for g in game.get('genres', []) if 'name' in g])
        platforms_str = json.dumps([p['name'] for p in game.get('platforms', []) if 'name' in p])
        themes_str = json.dumps([t['name'] for t in game.get('themes', []) if 'name' in t])
        dlcs_str = json.dumps([d['name'] for d in game.get('dlcs', []) if 'name' in d])
        player_perspectives_str = json.dumps([p['name'] for p in game.get('player_perspectives', []) if 'name' in p])  # NEW

        cover_url = game.get('cover', {}).get('url', '')

        websites = game.get('websites', [])
        steam_url = gog_url = playstation_url = xbox_url = epic_url = nintendo_url = official_url = None
        for site in websites:
            url = site.get('url', '')
            if 'steampowered.com' in url:
                steam_url = url
            elif 'gog.com' in url:
                gog_url = url
            elif 'playstation.com' in url:
                playstation_url = url
            elif 'xbox.com' in url:
                xbox_url = url
            elif 'epicgames.com' in url:
                epic_url = url
            elif 'nintendo.com' in url:
                nintendo_url = url
            elif site.get('category') == 1:  # Official
                official_url = url

        if not any([steam_url, gog_url, playstation_url, xbox_url, epic_url, nintendo_url, official_url]):
            continue

        cursor.execute(
            '''
            INSERT INTO GameData (
                game_id, name, summary, storyline, aggregated_rating, genres, platforms, themes,
                dlc_count, expansion_count, game_engines, involved_companies, keywords, similar_games,
                player_perspectives,
                release_date, release_date_human, dlcs,
                cover_url, steam_url, gog_url, playstation_url, xbox_url, epic_url, nintendo_url, official_url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (game_id) DO NOTHING;
            ''',
            (
                game.get('id'), game.get('name'), game.get('summary'), game.get('storyline'),
                game.get('aggregated_rating'), genres_str, platforms_str, themes_str,
                dlc_count, expansion_count, game_engines, involved_companies, keywords, similar_games,
                player_perspectives_str,  # NEW
                release_date, release_date_human, dlcs_str,
                cover_url, steam_url, gog_url, playstation_url, xbox_url, epic_url, nintendo_url, official_url
            )
        )

        if cursor.rowcount > 0:
            inserted_count += 1

    conn.commit()
    conn.close()
    return inserted_count


def get_data():
    access_token = get_access_token()
    headers = {
        "Client-ID": CLIENT_ID,
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }

    batch_size = 500
    offset = 0
    total_inserted = 0
    batch_number = 1

    while True:
        query = f"""
        fields id, name, summary, storyline, aggregated_rating,
        genres.name, platforms.name, themes.name,
        dlcs.name, expansions.name,
        game_engines.name, involved_companies.company.name,
        keywords.name, similar_games.name, player_perspectives.name,
        release_dates.date, release_dates.human,
        cover.url, websites.url, websites.category;
        where parent_game = null | parent_game != null & game_type = (0, 8, 9, 10);
        limit {batch_size}; offset {offset};
        """

        response = requests.post("https://api.igdb.com/v4/games", headers=headers, data=query)

        if response.status_code != 200:
            print(f"Error: {response.status_code}, {response.text}")
            break

        games = response.json()
        if not games:
            break

        inserted_count = insert_data(games)
        total_inserted += inserted_count

        print(f"Batch {batch_number}: Inserted {inserted_count} games")
        if batch_number % 10 == 0:
            print(f"Inserted so far: {total_inserted}")

        offset += batch_size
        batch_number += 1
        time.sleep(1)

    print(f"Total games inserted: {total_inserted}")


if __name__ == "__main__":
    create_database()
    get_data()