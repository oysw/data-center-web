from sklearn import tree

def calc(x, y):
    reg = tree.DecisionTreeRegressor()
    reg = reg.fit(x, y)
    return reg