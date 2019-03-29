from sklearn import neighbors
from sklearn.model_selection import cross_val_score
from hyperopt import hp, Trials, fmin, tpe, STATUS_OK
import numpy as np
import matplotlib.pyplot as plt

import base64
from io import BytesIO

x = 0
y = 0
reg = 0

def f(params):
    params['n_neighbors'] = int(params['n_neighbors'])
    global reg
    reg = neighbors.KNeighborsRegressor(**params)
    acc = cross_val_score(reg, x, y, cv=2, n_jobs=-1).mean()
    return {'loss': -acc, 'status': STATUS_OK}

def draw():
    global reg
    global x
    global y

    n_neighbors = reg.get_params()['n_neighbors']
    weights = reg.get_params()['weights']

    T = np.linspace(min(np.concatenate(x)), max(np.concatenate(x)), 2)[:, np.newaxis]
    y_ = reg.fit(x, y).predict(T)

    plt.scatter(x, y, c='k', label='data')
    plt.plot(T, y_, c='g', label='prediction')
    plt.axis('tight')
    plt.legend()
    plt.title("KNeighborsRegressor (k = %i, weights = '%s')" % (n_neighbors, weights))

    buffer = BytesIO()
    plt.savefig(buffer)
    plot_data = buffer.getvalue()
    imb = base64.b64encode(plot_data)
    ims = imb.decode()
    imd = "data:image/png;base64," + ims

    return imd

def calc(data_x, data_y):
    global x
    x = data_x
    global y
    y = data_y

    trials = 0
    best = 0
    img = ''

    space_rf = {
        'n_neighbors': hp.quniform('n_neighbors', 1, 2, 1),
        'weights': "uniform",
        'p': hp.quniform('q', 1, 10, 1),
    }

    trials_uni = Trials()
    best_uni = fmin(
        f,
        space=space_rf,
        algo=tpe.suggest,
        max_evals=50,
        trials=trials_uni
    )
    img_uni = draw()

    '''
    ############################################################
    '''
    space_rf['weights'] = "distance"

    trials_dis = Trials()
    best_dis = fmin(
        f,
        space=space_rf,
        algo=tpe.suggest,
        max_evals=50,
        trials=trials_dis
    )
    img_dis = draw()

    if trials_uni.losses()[-1] < trials_dis.losses()[-1]:
        trials = trials_uni
        best = best_uni
        img = img_uni
    else:
        trials = trials_dis
        best = best_dis
        img = img_dis

    return {"best": best, "trials": trials, "image": img}