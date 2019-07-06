from sklearn.svm import SVR
from sklearn.model_selection import cross_val_score
from hyperopt import hp, fmin,Trials, tpe, STATUS_OK

x = 0
y = 0
reg = 0


def f(param):
    global reg
    reg = SVR(**param, gamma="scale", cache_size=1000)
    acc = cross_val_score(reg, x, y, cv=5, n_jobs=-1).mean()
    return {"loss": -acc, "status": STATUS_OK}


def calc(data_x, data_y):
    global x
    x = data_x
    global y
    y = data_y
    global reg

    kernel_list = ["poly", "rbf", "sigmoid"]
    space_rf = {
        "kernel": hp.choice("kernel", kernel_list)
    }

    trials = Trials()
    best = fmin(
        f,
        space=space_rf,
        algo=tpe.suggest,
        max_evals=100,
        trials=trials
    )
    best["kernel"] = kernel_list[best["kernel"]]
    best_reg = SVR(**best)
    best_score = cross_val_score(best_reg, x, y, cv=5, n_jobs=-1).mean()
    return best_reg, best_score