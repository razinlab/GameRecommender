# Pixel Pusher - A Natural Language Game Recommender

[A web app](https://staging.dl8bwarntldti.amplifyapp.com/) to recommend games based on natural language input.

## Project Overview
Data has been fetched from the IGDB database user their API, narrowed down by the most import criteria. Data was organized, lightly cleaned, and then sent off to the cloud (Lambda Labs) to compute vector embeddings, this is for the user input to be compared against. User input is computed via the Jina AI API and then retrieved as vector embeddings in the same dimensions as the precomputed database. REST API construced with Flask for recommend, login, game save, and other functions. User data is stored via SQL tables. The backend code along with the data was Dockerized and then pushed to AWS for deployment. Frontend was deployed using AWS Amplify. Computations handled on AWS Lambda, user data stored on DynamoDB and API calls handled with API Gateway.

## Tools Used:
- Python, HTML, JavaScript
  - pandas, numpy, sklearn
- Flask
- AWS
  - Lambda
  - Amplify
  - DynamoDB
  - ECR
  - API Gateway
- Docker
- Jina AI API
- Jupyter

## Results
API calls, backend and frontend connection, game recommendation retrieval, etc. are all successful. User can input what they want to play in natural language and get back game recommendations, the function retrieves the top 50 and then selects a random 10 (for a better feeling of randomness).

## Possible Next Steps
- Clean up data further, a lot of junk games present and it is unclear which games are fluff and which games people would actually play. Difficult to do so as data must be offloaded to a cloud GPU instance for embedding.
- Greater filter options. Only way to retrieve games is via natural langauge, hardcoded options may be valuable for greater filtering.
