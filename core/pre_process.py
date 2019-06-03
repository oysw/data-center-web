"""
This file is used to process csv file
"""
import pandas as pd
from matminer.featurizers import structure


def preprocess(option, file):
    """
    Remove the NaN
    Change the columns of dataframe and calculate chemical features
    :return: Dataframe
    """
    try:
        file.seek(0)
        df = pd.read_pickle(file, compression=None)
    except Exception as e:
        print(e)
        try:
            file.seek(0)
            df = pd.read_json(file)
        except ValueError:
            try:
                file.seek(0)
                df = pd.read_csv(file)
            except Exception as e:
                print(e)
                return False, "File type is not supported"
    if not option:
        df = df.dropna(axis=0, how="all").dropna(axis=1)
    else:
        structure_info = option[0]
        option = option[1:]
        for i in option:
            featurizer = structure.__dict__[i]()
            try:
                df = featurizer.featurize_dataframe(df, structure_info)
            except Exception as e:
                file.close()
                return False, repr(e)
    file.close()
    return True, df
