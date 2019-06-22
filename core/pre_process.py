"""
This file is used to process csv file
"""
from django.utils.safestring import mark_safe
import pandas as pd
from core.models import Job
from django.core.cache import cache
from matminer.featurizers import structure
from matminer.featurizers import composition
from matminer.featurizers.conversions import StructureToComposition, StrToComposition
from pymatgen.core.structure import Structure


def backend_process(job_id, featurizer, target, value, choose_data):
    """
    New thread to process featurizer to avoid long time waiting in the front page.
    :param job_id:
    :param featurizer: (Conversion method)
    :param target: (Target column)
    :param value: (Extra parameter)
    :param choose_data: Raw data (For calculating and fitting) or uploaded data (For plotting)
    :return:
    """
    if cache.get("id_list") is None:
        cache.add("id_list", [], timeout=None)
    id_list = cache.get("id_list")
    id_list.append(job_id)
    cache.set("id_list", id_list, timeout=None)
    job = Job.objects.get(id=job_id)
    if choose_data == 'raw':
        file = job.raw
    elif choose_data == 'upload':
        file = job.upload
    else:
        return
    option = [featurizer, target, value]
    print("Process begin!")
    status, df = preprocess(option, file)
    # If the process of data succeeds without error reports, save new data in database.
    if status:
        file.open('wb')
        file.truncate()
        file.seek(0)
        df.to_pickle(file, compression=None)
        job.save()
        file.close()
        print("Caching begin!")
        html = mark_safe(df.to_html(classes=['table', 'table-striped', 'table-bordered', 'text-nowrap']))
        cache.set(str(job_id) + "_" + choose_data + "_html_graph", html)
    # Processing finished. Delete job id to enable extra more conversions of this data.
    id_list = cache.get("id_list")
    id_list.remove(job_id)
    cache.set("id_list", id_list, timeout=None)
    print("Process finished!")


def preprocess(option, file):
    """
    Convert the columns of dataframe and calculate chemical features
    The format of option is [featurizer, target-column, value].
    'featurizer' is the wanted way to process data.
    e.g. rename, strToStructure, structureToComposition, strToComposition
    'target-column' is the column to be processed.
    'value' is the extra needed parameter for featurizer
    e.g. 'rename' method needs new name to proceed.
    If empty list [] is provided, this function will only try to remove NaN columns and rows.
    :param: option (Parameters required by conversion)
    :param: File containing dataframe(Pandas class)
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
    if not option:
        df = df.dropna(axis=0, how="all").dropna(axis=1)
    else:
        featurizer = option[0]
        target = option[1]
        value = option[2]
        # Rename one column of dataframe.
        if featurizer == "rename":
            try:
                columns = list(df.columns)
                col_index = columns.index(target)
                columns.remove(target)
                columns.insert(col_index, value)
                df.columns = columns
            except Exception as e:
                return False, repr(e)
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
