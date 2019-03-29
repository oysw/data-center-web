import numpy as np

from . import decision_trees
from . import linear
from . import nearest_neighbors
from . import random_forests

def auto_ml(x, y):
    linear_reg = linear.calc(x, y)
    l_score = linear_reg['loss']
    decision_trees_reg = decision_trees.calc(x, y)
    dt_score = decision_trees_reg['trials'].losses()[-1]
    nearest_neighbors_reg = nearest_neighbors.calc(x, y)
    nn_score = nearest_neighbors_reg['trials'].losses()[-1]
    random_forests_reg = random_forests.calc(x, y)
    rf_score = random_forests_reg['trials'].losses()[-1]
    score = [l_score, dt_score, nn_score, rf_score]
    best = score.index(min(score))
    return [linear_reg, decision_trees_reg, nearest_neighbors_reg, random_forests_reg][best]

def file_read(x, y):
    data_x = np.load(x)
    data_y = np.load(y)
    return auto_ml(data_x, data_y)

if __name__ == '__main__':
    file_read("data_x.npy", "data_y.npy")
