from sklearn import linear_model
from sklearn.model_selection import cross_val_score
import numpy as np
import matplotlib.pyplot as plt

from io import BytesIO
import base64

def calc(x, y):
    reg = linear_model.LinearRegression()
    acc = cross_val_score(reg, x, y, cv=2, n_jobs=-1).mean()

    x_test = np.linspace(x.min(), x.max(), 2)[:, np.newaxis]
    y_pred = reg.fit(x, y).predict(x_test)

    plt.scatter(x, y, color='black', label='data')
    plt.plot(x_test, y_pred, color='blue', linewidth=3)
    plt.xlabel('data_x')
    plt.ylabel('data_y')
    plt.title('Python_Machine-LinearRegression')

    buffer = BytesIO()
    plt.savefig(buffer)
    plot_data = buffer.getvalue()
    imb = base64.b64encode(plot_data)
    ims = imb.decode()
    img = "data:image/png;base64," + ims

    return {"loss": -acc, "trials": '', "image": img}