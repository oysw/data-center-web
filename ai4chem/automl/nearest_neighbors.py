from sklearn.neighbors import KNeighborsRegressor
from sklearn.model_selection import cross_val_score
from hyperopt import hp, Trials, fmin, tpe, STATUS_OK

x = 0
y = 0
reg = 0


def f(params):
    global reg
    params['n_neighbors'] = int(params['n_neighbors'])
    reg = KNeighborsRegressor(**params)
    acc = cross_val_score(reg, x, y, cv=5, n_jobs=-1).mean()
    return {'loss': -acc, 'status': STATUS_OK}


def calc(data_x, data_y):
    global reg
    global x
    x = data_x
    global y
    y = data_y

    space_rf = {
        'n_neighbors': hp.quniform('n_neighbors', 1, x.shape[0]//2, 1),
    }

    trials = Trials()
    best = fmin(
        f,
        space=space_rf,
        algo=tpe.suggest,
        max_evals=100,
        trials=trials
    )
    best['n_neighbors'] = int(best['n_neighbors'])
    best_reg = KNeighborsRegressor(**best)
    best_score = cross_val_score(best_reg, x, y, cv=5, n_jobs=-1).mean()
    return best_reg, best_score
