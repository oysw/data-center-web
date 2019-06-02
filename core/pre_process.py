"""
This file is used to process .xyz file to meet the shape requirement of auto_ml
"""
import re
import os
import pickle as pkl
import numpy as np
import pandas as pd
from io import StringIO
from django.core.files import File
from matminer.featurizers import structure


def xyz_process(xyz_file):
    """
    This function is used to transform .xyz file (Atom types and Atoms' coordinations).
    :param xyz_file:
    :return:
    """
    path = os.path.abspath(__file__)
    path = os.path.dirname(path)
    path = os.path.join(path, "periodic_table")
    with open(path, "rb") as _f:
        periodic_table = pkl.load(_f)

    p_table = {}
    for item in periodic_table:
        p_table[item[0]] = [item[1], item[2]]

    feature = []
    target = []

    with open(xyz_file.name, "r") as _f:
        is_another_frame = False
        frame_feature = []
        while True:
            if is_another_frame:
                if not frame_feature:
                    feature.append(frame_feature)
                frame_feature = []
                is_another_frame = False
            line = _f.readline()
            if line == '':
                break
            line = line.rstrip("\n").strip(" ")
            pattern = re.compile(r" +")
            info = re.split(pattern, line)
            if len(info) > 4:
                target.append([float(info[-1])])
                is_another_frame = True
                continue
            elif len(info) < 4:
                continue
            atom_w = p_table[info[0]][1]
            _x = float(info[1])
            _y = float(info[2])
            _z = float(info[3])
            coordinate = np.mean([_x, _y, _z])
            frame_feature.append(coordinate * atom_w)
        feature.append(frame_feature)

    feature = np.array(feature)
    target = np.array(target)
    return feature, target


def csv_preprocess(option, file):
    """
    Remove the NaN
    Change the columns of dataframe and calculate chemical features
    :return: html
    """
    try:
        file.seek(0)
        df = pd.read_csv(file)
    except AttributeError as e:
        return False, e
    except UnicodeDecodeError as e:
        return False, e
    if not option:
        df = df.dropna(axis=0, how="all").dropna(axis=1)
    else:
        structure_info = option[0]
        for i in option:
            featurizer = structure.__dict__[i]()
            df = featurizer.featurize_dataframe(df, structure_info)
    html = df.to_html()
    return True, html
