"""
This file is used to process the data after training.
"""
import os
import numpy as np
from dsweb.settings import MEDIA_ROOT


def predict_file_create(y_predict, username):
    """
    Generate pure text file containing predict data.
    The file is saved in /tmp/ai4chem/predict/
    :param y_predict:
    :return: The name of predicted values' file
    """
    predict_dir = MEDIA_ROOT + 'predict/'
    try:
        os.makedirs(predict_dir)
    except FileExistsError:
        pass
    predict_file = predict_dir + username + '.txt'
    np.savetxt(predict_file, y_predict, fmt="%f", delimiter=',')
