import numpy as np
from numpy.linalg import norm

def cosine_similarity(a,b_matrix):
  scores = b_matrix @ a / (norm(b_matrix, axis=1) * norm(a))                                                             
  return scores 