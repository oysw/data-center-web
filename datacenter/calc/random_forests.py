from sklearn.ensemble import RandomForestRegressor

def calc(x, y, n):
    reg = RandomForestRegressor(n_estimators=n)
    reg = reg.fit(x, y)
    return reg
