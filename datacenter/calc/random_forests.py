from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_score
from hyperopt import hp, tpe, fmin, Trials, STATUS_OK

x = 0
y = 0

def f(params):
    params['n_estimators'] = int(params['n_estimators'])
    reg = RandomForestRegressor(**params)
    acc = cross_val_score(reg, x, y, cv=2, n_jobs=-1).mean()
    return {'loss': -acc, 'status': STATUS_OK}

def calc(data_x, data_y):
    space_rf = {
        'n_estimators': hp.quniform('n_estimators', 1, 500, 1),
        'criterion': hp.choice('criterion', ["mse", "mae"]),
        'max_features': hp.choice('max_features', ["auto"]),
        # 'bootstrap': hp.choice('bootstrap ', [True, False]),
        'oob_score': hp.choice('oob_score ', [True, False]),
        'warm_start': hp.choice('warm_start', [True, False]),
    }

    global x
    x = data_x
    global y
    y = data_y

    trials = Trials()
    best = fmin(
        f,
        space=space_rf,
        algo=tpe.suggest,
        max_evals=50,
        trials=trials
    )
    return {"best": best, "trials": trials}
