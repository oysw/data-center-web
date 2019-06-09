from . import linear
from . import nearest_neighbors
from . import random_forests
from . import svr
from . import multi_layer_perception


def auto_ml(x, y):
    """
    This function could be developed separately.
    :param x:
    :param y:
    :return:
    """
    linear_reg, l_score = linear.calc(x, y)
    nearest_neighbors_reg, nn_score = nearest_neighbors.calc(x, y)
    random_forests_reg, rf_score = random_forests.calc(x, y)
    sv_reg, svr_score = svr.calc(x, y)
    mpl_reg, mpl_score = multi_layer_perception.calc(x, y)

    mod = [linear_reg, nearest_neighbors_reg, random_forests_reg, sv_reg, mpl_reg]
    score = [l_score, nn_score, rf_score, svr_score, mpl_score]

    # Ranking by score.
    index = score.index(max(score))
    best = mod[index]
    print(best.__class__.__name__)

    return best.fit(x, y)
