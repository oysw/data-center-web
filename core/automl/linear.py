from sklearn.linear_model import LinearRegression
from sklearn.model_selection import cross_val_score


def calc(x, y):
    reg = LinearRegression()
    acc = cross_val_score(reg, x, y, cv=5, n_jobs=-1).mean()

    return LinearRegression(), acc
