from sklearn.neural_network import MLPRegressor
from sklearn.model_selection import cross_val_score
from hyperopt import hp, fmin, tpe, Trials, STATUS_OK

x = 0
y = 0
reg = 0

def set_hidden_layer(param):
    layer_one = int(param["layer_one"])
    layer_two = int(param["layer_two"])
    layer_three = int(param["layer_three"])
    hidden_layer = (layer_one, layer_two, layer_three)
    return MLPRegressor(hidden_layer_sizes=hidden_layer, max_iter=1200)


def f(param):
    global reg
    reg = set_hidden_layer(param)
    acc = cross_val_score(reg, x, y, cv=5, n_jobs=-1).mean()
    return {"loss": -acc, "status": STATUS_OK}


def calc(data_x, data_y):
    global x
    global y
    global reg
    x = data_x
    y = data_y

    space_rf = {
        'layer_one': hp.quniform('layer_one', 1, 100, 1),
        'layer_two': hp.quniform('layer_two', 1, 100, 1),
        'layer_three': hp.quniform('layer_three', 1, 100, 1),
    }

    trials = Trials()
    best = fmin(
        f,
        space=space_rf,
        algo=tpe.suggest,
        max_evals=100,
        trials=trials
    )
    best_reg = set_hidden_layer(best)
    best_score = cross_val_score(best_reg, x, y, cv=5, n_jobs=-1).mean()
    return best_reg, best_score