"""
This file is used to process csv file
"""
import pandas as pd
from matminer.featurizers import structure
from matminer.featurizers import composition
from matminer.featurizers.conversions import StructureToComposition
from pymatgen.core.structure import Structure


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
        if structure_info == "rename":
            columns = list(df.columns)
            col_index = columns.index(option[0])
            columns.remove(option[0])
            columns.insert(col_index, option[1])
            df.columns = columns
            file.close()
            return True, df
        elif structure_info == "strToStructure":
            target_col = option[0]
            try:
                df[target_col] = [Structure.from_str(i, 'json') for i in df[target_col]]
            except Exception as e:
                file.close()
                return False, repr(e)
            file.close()
            return True, df
        elif structure_info == "structureToComposition":
            target_col = option[0]
            try:
                df = StructureToComposition().featurize_dataframe(df, target_col)
            except Exception as e:
                file.close()
                return False, repr(e)
            file.close()
            return True, df
        for i in option:
            try:
                featurizer = structure.__dict__[i]()
            except KeyError:
                try:
                    featurizer = composition.__dict__[i]()
                except KeyError:
                    break
            try:
                df = featurizer.featurize_dataframe(df, structure_info)
            except Exception as e:
                file.close()
                return False, repr(e)
    file.close()
    return True, df
