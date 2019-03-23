import numpy as np

from . import decision_trees
from . import linear
from . import nearest_neighbors
from . import random_forests

def decision_tree_calc(x, y):
    result = decision_trees.calc(x, y)
    return result

def linear_regression(x, y):
    result = linear.calc(x, y)
    return result

def nearest_neighbors_calc(x, y):
    k = 15
    weight = 'uniform'
    result = nearest_neighbors.calc(x, y, k, weight)
    return result

def random_forests_calc(x, y):
    n = 10
    result = random_forests.calc(x, y, n)
    return result

def auto_ml(x, y):
    result = {}
    result.update(linear_reg=linear_regression(x, y))
    result.update(decision_tree=decision_tree_calc(x, y))
    result.update(nearest_nei=nearest_neighbors_calc(x, y))
    result.update(random_for=random_forests_calc(x, y))
    return result

def file_read(x, y):
    data_x = np.load(x)
    data_y = np.load(y)
    return auto_ml(data_x, data_y)

if __name__ == '__main__':
    file_read("data_x.npy", "data_y.npy")
