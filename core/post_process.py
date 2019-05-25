"""
This file is used to process the data after training.
"""
import os
import numpy as np
from django.utils.crypto import get_random_string
from dsweb.settings import MEDIA_ROOT


def predict_file_create(y_predict):
    """
    Generate csv file containing predict data.
    :param y_predict:
    :return: The name of predicted values' file
    """
    predict_dir = MEDIA_ROOT + 'predict'
    try:
        os.makedirs(predict_dir)
    except FileExistsError:
        pass
    random_string = get_random_string(7)
    predict_file = predict_dir + '/predict_' + random_string + '.txt'

    np.savetxt(predict_file, y_predict, fmt="%f", delimiter=',')
    return 'predict_' + random_string + '.txt'
