from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_score
from hyperopt import hp, tpe, fmin, Trials, STATUS_OK
import numpy as np
import matplotlib.pyplot as plt

from io import BytesIO
import base64

x = 0
y = 0
reg = 0

def f(params):
    global reg
    params['n_estimators'] = int(params['n_estimators'])
    reg = RandomForestRegressor(**params)
    acc = cross_val_score(reg, x, y, cv=2, n_jobs=-1).mean()
    return {'loss': -acc, 'status': STATUS_OK}

def draw():
    global reg
    global x
    global y

    x_test = np.linspace(min(np.concatenate(x)), max(np.concatenate(x)), 2)[:, np.newaxis]
    y_pred = reg.fit(x, y).predict(x_test)

    plt.scatter(x, y, color='darkorange', label='data')

    plt.plot(x_test, y_pred, color='g', label='RandomForestRegressor')
    plt.xlabel('data_x')
    plt.ylabel('data_y')
    plt.title('Python_Machine-learning_RandomForest')
    plt.legend()

    buffer = BytesIO()
    plt.savefig(buffer)
    plot_data = buffer.getvalue()
    imb = base64.b64encode(plot_data)
    ims = imb.decode()
    imd = "data:image/png;base64," + ims

    return imd

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

    img = draw()

    return {"best": best, "trials": trials, "image": img}
