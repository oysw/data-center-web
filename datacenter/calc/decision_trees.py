import numpy as np
from sklearn import tree
from sklearn.model_selection import cross_val_score
from hyperopt import hp, Trials, fmin, tpe, STATUS_OK
import matplotlib.pyplot as plt

import base64
from io import BytesIO

x = 0
y = 0
reg = 0

def f(params):
    global reg
    reg = tree.DecisionTreeRegressor(**params)
    acc = cross_val_score(reg, x, y, cv=2, n_jobs=-1).mean()
    return {'loss': -acc, 'status': STATUS_OK}

def draw():
    global reg
    reg.fit(x, y)
    x_test = np.arange(min(x), max(x), 0.01)[:, np.newaxis]
    y_pred = reg.predict(x_test)

    plt.figure()
    plt.scatter(x, y, s=20, edgecolor="black", c="darkorange", label="data")
    plt.plot(x_test, y_pred, color="cornflowerblue", label="max_depth=2", linewidth=2)
    plt.xlabel("data")
    plt.ylabel("target")
    plt.title("Decision Tree Regression")
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

    return {'best': best, 'trials': trials, "image": draw()}