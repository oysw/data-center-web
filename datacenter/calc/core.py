import numpy as np

from . import decision_trees
from . import linear
from . import nearest_neighbors
from . import random_forests

def decision_tree_calc(x, y):
    result = decision_trees.calc(x, y)
    print(result)

def linear_regression(x, y):
    result = linear.calc(x, y)
    print(result)

def nearest_neighbors_calc(x, y):
    k = 15
    weight = 'uniform'
    result = nearest_neighbors.calc(x, y, k, weight)
    print(result)

def random_forests_calc(x, y):
    n = 10
    result = random_forests.calc(x, y, n)
    print(result)

def auto_ml(x, y):
    linear_regression(x, y)
    decision_tree_calc(x, y)
    nearest_neighbors_calc(x, y)
    random_forests_calc(x, y)

def file_read(x, y):
    data_x = np.load(x)
    data_y = np.load(y)
    auto_ml(data_x, data_y)

if __name__ == '__main__':
    file_read("data_x.npy", "data_y.npy")
