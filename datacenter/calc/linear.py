from sklearn import linear_model

def calc(x, y):
    reg = linear_model.LinearRegression()
    reg = reg.fit(x, y)
    return reg