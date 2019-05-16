import re
import os
import numpy as np
import pickle as pkl


def preprocess(xyz_file):
    path = os.path.abspath(__file__)
    path = os.path.dirname(path)
    path = os.path.join(path, "periodic_table")
    with open(path, "rb") as f:
        periodic_table = pkl.load(f)

    p_table = {}
    for item in periodic_table:
        p_table[item[0]] = [item[1], item[2]]

    feature = []
    target = []

    with open(xyz_file.name, "r") as f:
        is_another_frame = False
        frame_feature = []
        while True:
            if is_another_frame:
                if len(frame_feature) != 0:
                    feature.append(frame_feature)
                frame_feature = []
                is_another_frame = False
            line = f.readline()
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
            x = float(info[1])
            y = float(info[2])
            z = float(info[3])
            coordinate = np.mean([x, y, z])
            frame_feature.append(coordinate * atom_w)
        feature.append(frame_feature)

    feature = np.array(feature)
    target = np.array(target)
    return feature, target
