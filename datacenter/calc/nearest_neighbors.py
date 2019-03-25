from sklearn import neighbors
from sklearn.model_selection import cross_val_score
from hyperopt import hp, Trials, fmin, tpe, STATUS_OK

x = 0
y = 0

def f(params):
    params['n_neighbors'] = int(params['n_neighbors'])
    reg = neighbors.KNeighborsRegressor(**params)
    acc = cross_val_score(reg, x, y, cv=2).mean()
    return {'loss': -acc, 'status': STATUS_OK}

def calc(data_x, data_y):
    global x
    x = data_x
    global y
    y = data_y

    space_rf = {
        'n_neighbors': hp.quniform('n_neighbors', 1, x.shape[1], 1),
        'weights': hp.choice('weights', ["uniform", "distance"]),
        'p': hp.quniform('q', 1, 10, 1),
    }

    trials = Trials()
    best = fmin(
        f,
        space=space_rf,
        algo=tpe.suggest,
        max_evals=50,
        trials=trials
    )

    return {"best": best, "trials": trials}