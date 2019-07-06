from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_score
from hyperopt import hp, tpe, fmin, Trials, STATUS_OK

x = 0
y = 0
reg = 0


def f(params):
    global reg
    params['n_estimators'] = int(params['n_estimators'])
    reg = RandomForestRegressor(**params)
    acc = cross_val_score(reg, x, y, cv=5, n_jobs=-1).mean()
    return {'loss': -acc, 'status': STATUS_OK}


def calc(data_x, data_y):
    global reg
    global x
    x = data_x
    global y
    y = data_y

    space_rf = {
        'n_estimators': hp.quniform('n_estimators', 1, 100, 1),
    }

    trials = Trials()
    best = fmin(
        f,
        space=space_rf,
        algo=tpe.suggest,
        max_evals=100,
        trials=trials
    )
    best['n_estimators'] = int(best['n_estimators'])
    best_reg = RandomForestRegressor(**best)
    best_score = cross_val_score(RandomForestRegressor(**best), x, y, cv=5, n_jobs=-1).mean()
    return best_reg, best_score 
    