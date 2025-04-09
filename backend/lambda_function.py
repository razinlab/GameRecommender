import awsgi
from app import app
import boto3
import os

os.environ['EMBEDDINGS_PATH'] = '/tmp/game_embeddings.npy'
os.environ['GAMES_PATH'] = '/tmp/GameData.csv'


def init():
    s3 = boto3.client('s3')
    bucket_name = os.environ.get('S3_BUCKET_NAME')

    try:
        s3.download_file(bucket_name, 'data/game_embeddings.npy', '/tmp/game_embeddings.npy')
        print(f"Successfully downloaded embeddings from s3://{bucket_name}/data/game_embeddings.npy")

        s3.download_file(bucket_name, 'data/GameData.csv', '/tmp/GameData.csv')
        print(f"Successfully downloaded game data from s3://{bucket_name}/data/GameData.csv")

        return True
    except Exception as e:
        print(f"Error downloading files from S3: {str(e)}")
        return False


def lambda_handler(event, context):
    if not os.path.exists('/tmp/game_embeddings.npy'):
        if not init():
            return {
                'statusCode': 500,
                'body': '{"error": "Failed to initialize - could not download required files"}'
            }

    return awsgi.response(app, event, context)