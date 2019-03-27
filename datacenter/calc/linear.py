from sklearn import linear_model
from sklearn.model_selection import cross_val_score

def calc(x, y):
    reg = linear_model.LinearRegression()
    acc = cross_val_score(reg, x, y, cv=2, n_jobs=-1).mean()
    return -acc