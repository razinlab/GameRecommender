from flask import Flask, request, jsonify
from flask_cors import CORS
from recommender import get_recommendations
import hashlib
import secrets
import jwt
import datetime
from functools import wraps
import os
import boto3
from botocore.exceptions import ClientError
import json
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
CORS(app)
app.wsgi_app = ProxyFix(app.wsgi_app)

SECRET_KEY = os.environ.get('JWT_SECRET_KEY', secrets.token_hex(16))

dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('AWS_REGION', 'us-east-2'))

USERS_TABLE = os.environ.get('USERS_TABLE', 'game_recommender_users')
SAVED_GAMES_TABLE = os.environ.get('SAVED_GAMES_TABLE', 'game_recommender_saved_games')


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            token = auth_header.split(" ")[1] if auth_header.startswith("Bearer ") else auth_header

        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except:
            return jsonify({'message': 'Token is invalid!'}), 401

        return f(*args, **kwargs)

    return decorated


def get_user_from_token():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None

    token = auth_header.split(' ')[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except:
        return None


@app.route('/recommend', methods=['POST'])
def recommend():
    data = request.get_json()
    query = data.get('query', '')
    results = get_recommendations(query)
    return jsonify({"results": results})


@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Missing username or password'}), 400

    username = data.get('username')
    password = data.get('password')

    users_table = dynamodb.Table(USERS_TABLE)

    try:
        response = users_table.get_item(
            Key={'username': username}
        )

        if 'Item' in response:
            return jsonify({'message': 'Username already exists'}), 409

        hashed_password = hash_password(password)
        user_id = secrets.token_hex(8)

        users_table.put_item(
            Item={
                'username': username,
                'user_id': user_id,
                'password_hash': hashed_password,
                'created_at': datetime.datetime.utcnow().isoformat()
            }
        )

        return jsonify({'message': 'User registered successfully'}), 201

    except ClientError as e:
        print(e.response['Error']['Message'])
        return jsonify({'message': 'Database error'}), 500


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Missing username or password'}), 400

    username = data.get('username')
    password = data.get('password')

    users_table = dynamodb.Table(USERS_TABLE)

    try:
        response = users_table.get_item(
            Key={'username': username}
        )

        if 'Item' not in response or response['Item']['password_hash'] != hash_password(password):
            return jsonify({'message': 'Invalid username or password'}), 401

        user = response['Item']

        token = jwt.encode({
            'user_id': user['user_id'],
            'username': username,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
        }, SECRET_KEY, algorithm="HS256")

        return jsonify({'token': token}), 200

    except ClientError as e:
        print(e.response['Error']['Message'])
        return jsonify({'message': 'Database error'}), 500


@app.route('/saved-games', methods=['POST'])
@token_required
def save_game():
    user = get_user_from_token()
    if not user:
        return jsonify({'message': 'Invalid token'}), 401

    data = request.get_json()

    if not data or not data.get('game_id') or not data.get('game_name'):
        return jsonify({'message': 'Missing game information'}), 400

    game_id = data.get('game_id')
    game_name = data.get('game_name')
    game_url = data.get('game_url', '')
    image_url = data.get('image_url', '')
    steam_url = data.get('steam_url', '')
    gog_url = data.get('gog_url', '')
    xbox_url = data.get('xbox_url', '')
    playstation_url = data.get('playstation_url', '')
    epic_url = data.get('epic_url', '')
    nintendo_url = data.get('nintendo_url', '')
    official_url = data.get('official_url', '')

    saved_games_table = dynamodb.Table(SAVED_GAMES_TABLE)

    try:
        response = saved_games_table.get_item(
            Key={
                'user_id': user['user_id'],
                'game_id': game_id
            }
        )

        if 'Item' in response:
            return jsonify({'message': 'Game already saved'}), 409

        saved_games_table.put_item(
            Item={
                'user_id': user['user_id'],
                'game_id': game_id,
                'game_name': game_name,
                'game_url': game_url,
                'image_url': image_url,
                'steam_url': steam_url,
                'gog_url': gog_url,
                'xbox_url': xbox_url,
                'playstation_url': playstation_url,
                'epic_url': epic_url,
                'nintendo_url': nintendo_url,
                'official_url': official_url,
                'saved_at': datetime.datetime.utcnow().isoformat()
            }
        )

        return jsonify({'message': 'Game saved successfully'}), 201

    except ClientError as e:
        print(e.response['Error']['Message'])
        return jsonify({'message': f'Database error: {str(e)}'}), 500


@app.route('/saved-games', methods=['GET'])
@token_required
def get_saved_games():
    user = get_user_from_token()
    if not user:
        return jsonify({'message': 'Invalid token'}), 401

    saved_games_table = dynamodb.Table(SAVED_GAMES_TABLE)

    try:
        response = saved_games_table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('user_id').eq(user['user_id'])
        )

        games = []
        for item in response.get('Items', []):
            games.append({
                'game_id': item.get('game_id'),
                'game_name': item.get('game_name'),
                'game_url': item.get('game_url'),
                'image_url': item.get('image_url'),
                'steam_url': item.get('steam_url'),
                'gog_url': item.get('gog_url'),
                'xbox_url': item.get('xbox_url'),
                'playstation_url': item.get('playstation_url'),
                'epic_url': item.get('epic_url'),
                'nintendo_url': item.get('nintendo_url'),
                'official_url': item.get('official_url')
            })

        return jsonify({'games': games}), 200

    except ClientError as e:
        print(e.response['Error']['Message'])
        return jsonify({'message': 'Database error'}), 500



@app.route('/saved-games/<game_id>', methods=['DELETE'])
@token_required
def remove_saved_game(game_id):
    user = get_user_from_token()
    if not user:
        return jsonify({'message': 'Invalid token'}), 401

    saved_games_table = dynamodb.Table(SAVED_GAMES_TABLE)

    try:
        saved_games_table.delete_item(
            Key={
                'user_id': user['user_id'],
                'game_id': game_id
            }
        )

        return jsonify({'message': 'Game removed successfully'}), 200

    except ClientError as e:
        print(e.response['Error']['Message'])
        return jsonify({'message': 'Database error'}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)