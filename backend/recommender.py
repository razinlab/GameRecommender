import numpy as np
import requests
import pandas as pd
import os
from scipy.spatial.distance import cosine

API_KEY =

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

default_embeddings_path = os.path.join(BASE_DIR, 'data', 'game_embeddings.npy')
default_games_path = os.path.join(BASE_DIR, 'data', 'GameData.csv')

embeddings_path = os.environ.get('EMBEDDINGS_PATH', default_embeddings_path)
games_path = os.environ.get('GAMES_PATH', default_games_path)


game_embeddings = np.load(embeddings_path)
games = pd.read_csv(games_path)


def cosine_similarity(a, b):
    """Calculate cosine similarity between vectors"""
    return 1 - cosine(a, b)


def get_recommendations(prompt: str, search_k=50, final_k=10):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "input": prompt,
        "model": "jina-embeddings-v3",
        "dimensions": 1024
    }

    response = requests.post(
        "http://api.jina.ai/v1/embeddings",
        headers=headers,
        json=data
    )
    response.raise_for_status()

    prompt_embedding = np.array(response.json()["data"][0]["embedding"]).astype("float32")

    similarities = np.array([cosine_similarity(prompt_embedding, emb) for emb in game_embeddings])

    top_indices = np.argsort(similarities)[-search_k:][::-1]

    if len(top_indices) > final_k:
        random_indices = np.random.choice(top_indices, size=final_k, replace=False)
    else:
        random_indices = top_indices

    LINK_COLUMNS = {
        "steam": "steam_url",
        "gog": "gog_url",
        "xbox": "xbox_url",
        "playstation": "playstation_url",
        "epic": "epic_url",
        "nintendo": "nintendo_url",
        "official": "official_url"
    }

    results = []
    for i in random_indices:

        image_url = (
            games["cover_url"][i]
            if "cover_url" in games.columns and pd.notna(games["cover_url"][i])
            else None
        )

        links = {}
        for label, col in LINK_COLUMNS.items():
            if col in games.columns:
                value = games[col][i]
                if pd.notna(value) and str(value).strip() != "":
                    links[label] = value

        results.append({
            "text": games["name"][i],
            "image_url": image_url,
            "links": links
        })

    return results



def generate_game_embeddings(games_df, output_path):
    """
    Generate embeddings for all games and save to file

    Args:
        games_df: DataFrame with game data including descriptions
        output_path: Where to save the numpy array of embeddings
    """
    all_embeddings = []

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    for i, game in games_df.iterrows():
        text_to_embed = f"{game['name']} {game.get('description', '')}"

        data = {
            "input": text_to_embed,
            "model": "jina-embeddings-v3",
            "dimensions": 1024
        }

        response = requests.post(
            "http://api.jina.ai/v1/embeddings",
            headers=headers,
            json=data
        )
        response.raise_for_status()

        embedding = np.array(response.json()["data"][0]["embedding"]).astype("float32")
        all_embeddings.append(embedding)

        if (i + 1) % 10 == 0:
            print(f"Processed {i + 1}/{len(games_df)} games")

    np.save(output_path, np.array(all_embeddings))
    print(f"Saved {len(all_embeddings)} embeddings to {output_path}")