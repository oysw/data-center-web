from sklearn import neighbors

def calc(x, y, k, weight):
    reg = neighbors.KNeighborsRegressor(n_neighbors=k, weights=weight)
    reg = reg.fit(x, y)
    return reg