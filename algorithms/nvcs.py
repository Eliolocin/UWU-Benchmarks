import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

class NVCS:
    def __init__(self):
        pass
    
    # Generates n-grams from the given text. 
    # (e.g., "apple", 2) -> ["ap", "pp", "pl", "le"]
    def generate_ngrams(self, text, n):
        return [text[i:i+n] for i in range(len(text)-n+1)]
    
    # Creates a sorted vocabulary of n-grams from the provided texts. 
    # (e.g., "apple", "banana", 2) -> ["an", "ap", "ba", "le", "na", "pl", "pp"]
    def create_vocabulary(self, *texts, n):
        vocab = set()
        for text in texts:
            vocab.update(self.generate_ngrams(text, n))
        return sorted(vocab)

    # Converts the given text into a vector based on the provided vocabulary of n-grams. 
    # (e.g., "apple", ["an", "ap", "ba", "le", "na", "pl", "pp"], 2) -> [0, 1, 0, 1, 0, 1, 1]
    # (e.g., "banana", ["an", "ap", "ba", "le", "na", "pl", "pp"], 2) -> [2, 0, 1, 0, 2, 0, 0]
    def vectorize(self, text, vocab, n):
        ngrams = self.generate_ngrams(text, n)
        vector = [ngrams.count(gram) for gram in vocab]
        return vector

    # Calculates the cosine similarity between two vectors. 
    # (eg., [0, 1, 0, 1, 0, 1], [0, 1, 0, 1, 0, 1]) -> 1.0
    def cosine_sim(self, vec1, vec2):
        vec1 = np.array(vec1).reshape(1, -1)
        vec2 = np.array(vec2).reshape(1, -1)
        return cosine_similarity(vec1, vec2)[0][0]

    # Calculates the N-Gram Vector Cosine Similarity (NVCS) score between two texts using n-grams.
    def calculate_nvcs(self, ngram, text1, text2):
        vocab = self.create_vocabulary(text1, text2, n=ngram)
        vec1 = self.vectorize(text1, vocab, ngram)
        vec2 = self.vectorize(text2, vocab, ngram)
        nvcs_score = self.cosine_sim(vec1, vec2)
        print(f"Sample Dialogue's N-Grams: {vec1}")
        print(f"Generated Responses' N-Grams: {vec1}")
        return float(nvcs_score)
    
