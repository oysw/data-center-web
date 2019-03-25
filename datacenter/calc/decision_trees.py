from sklearn import tree
from sklearn.model_selection import cross_val_score
from hyperopt import hp, Trials, fmin, tpe, STATUS_OK

x = 0
y = 0

def f(params):
    reg = tree.DecisionTreeRegressor(**params)
    acc = cross_val_score(reg, x, y, cv=2).mean()
    return {'loss': -acc, 'status': STATUS_OK}

def calc(data_x, data_y):
    space_rf = {
        'criterion': hp.choice('criterion', ["mse", "friedman_mse", "mae"]),
        'max_depth': hp.choice('max_depth', range(1, 20)),
        'max_features': hp.choice('max_features ', ["auto"]),
    }
    global x
    x = data_x
    global y
    y = data_y

    trials = Trials()
    best = fmin(f,
                space=space_rf,
                algo=tpe.suggest,
                max_evals=50,
                trials=trials
                )
    return {'best': best, 'trials': trials}