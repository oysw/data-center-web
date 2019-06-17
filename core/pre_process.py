"""
This file is used to process csv file
"""
import pandas as pd
from matminer.featurizers import structure
from matminer.featurizers import composition
from matminer.featurizers.conversions import StructureToComposition, StrToComposition
from pymatgen.core.structure import Structure


def preprocess(option, file):
    """
    Remove the NaN
    Change the columns of dataframe and calculate chemical features
    :return: Dataframe
    """
    try:
        # The file may be json, csv and pickle format.
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
                return False, repr(e)
    finally:
        file.close()
    """
    The format of option is [featurizer, target column, value].
    'featurizer' is the wanted way to process data.
    If empty list [] is provided, this function will only try to remove NaN columns and rows.
    """
    if not option:
        df = df.dropna(axis=0, how="all").dropna(axis=1)
    else:
        featurizer = option[0]
        target = option[1]
        value = option[2]
        # Rename one column of dataframe.
        if featurizer == "rename":
            columns = list(df.columns)
            col_index = columns.index(target)
            columns.remove(target)
            columns.insert(col_index, value)
            df.columns = columns
        # Convert json format string to structure(Pymatgen class)
        elif featurizer == "strToStructure":
            try:
                df[target] = [Structure.from_str(i, 'json') for i in df[target]]
            except Exception as e:
                return False, repr(e)
        # Convert structure(Pymatgen class) to composition(Pymatgen class)
        elif featurizer == "structureToComposition":
            try:
                df = StructureToComposition().featurize_dataframe(df, target)
            except Exception as e:
                return False, repr(e)
        # Convert string to composition(Pymatgen class)
        elif featurizer == "strToComposition":
            try:
                df = StrToComposition().featurize_dataframe(df, target)
            except Exception as e:
                return False, repr(e)
        else:
            try:
                # Provided by matminer to process structure(Pymatgen class).
                convert = structure.__dict__[featurizer]()
            except KeyError:
                try:
                    # Provide by matminer to process composition(Pymatgen class).
                    convert = composition.__dict__[featurizer]()
                except KeyError:
                    df = space_check(df)
                    return True, df
            try:
                df = convert.featurize_dataframe(df, target)
            except Exception as e:
                return False, repr(e)
    df = space_check(df)
    return True, df


def space_check(dataframe):
    """
    Since it's hard for form submission if there are spaces, and there may be unpredictable error on the
    front-end page, we need to convert space to _.
    :param dataframe:
    :return:
    """
    df = dataframe
    columns = list(df.columns)
    new_col = []
    for i in columns:
        new_col.append(i.replace(" ", "_"))
    df.columns = new_col
    return df
