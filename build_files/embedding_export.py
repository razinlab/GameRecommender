
import faiss
import numpy as np


index = faiss.read_index('C:/Users/razin/PycharmProjects/GameRecommenderApp/data/index')


dimension = index.d  # Get embedding dimension
num_vectors = index.ntotal  # Get number of vectors

embeddings = np.zeros((num_vectors, dimension), dtype=np.float32)


for i in range(num_vectors):
    embeddings[i] = index.reconstruct(i)


np.save('game_embeddings.npy', embeddings)