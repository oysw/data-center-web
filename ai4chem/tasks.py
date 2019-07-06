from __future__ import absolute_import, unicode_literals
import time
import multiprocessing as mp
from io import BytesIO
import pandas as pd
import joblib
from celery import shared_task
from django.core.files import File
from django.utils.crypto import get_random_string
from django.utils.safestring import mark_safe
from django.core.cache import cache
from ai4chem.models import Job
from .tools import job_error, preprocess
from ai4chem.automl.auto_ml import auto_ml


@shared_task
def calculate(job_id):
    """
    Analyze the data and save the machine learning models provided by sklearn.
    Currently involved models:
        Regression：
            Linear, Nearest Neighbour, Random Forests, Support Vectors Machine, Multiple Layers Perception.
        Classification:
            None
    :return:
    """
    try:
        job = Job.objects.get(id=job_id)
    except Job.DoesNotExist:
        return
    try:
        data = pd.read_pickle(job.raw, compression=None)
    except Exception as e:
        job_error(job, e)
        return
    job.status = 'C'
    job.save()
    try:
        x = data[data.columns[0: -1]]
        y = data[data.columns[-1]]
        print("********* Calculation begins *********")
        current_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        print("********* " + current_time + " *********")
        mp.current_process().daemon = False
        mod = auto_ml(x, y)
        current_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        print("********* " + current_time + " *********")
        print("********* Calculation ends *********")
    except Exception as e:
        job_error(job, e)
        return
    temp = BytesIO()
    joblib.dump(mod, temp)
    model_file = File(temp)
    model_file.name = 'model_' + get_random_string(7)
    # Save result
    job.mod = model_file
    job.status = 'F'
    job.save()
    return


@shared_task
def featurize(option):
    """
    Convert the dataframe with assigned featurizer and update the database with new dataframe.
    Writing new table html-format code into cache.
    :return:
    """
    job_id, featurizer, target, value, choose_data = option
    job = Job.objects.get(id=job_id)
    if choose_data == 'raw':
        file = job.raw
    elif choose_data == 'upload':
        file = job.upload
    else:
        return
    option = [featurizer, target, value]
    print("Process {} for job {} begin!".format(featurizer, job_id))
    mp.current_process().daemon = False
    status, df = preprocess(option, file)
    # If the process of data succeeds without error reports, save new data in database.
    if status:
        file.open('wb')
        file.truncate()
        file.seek(0)
        df.to_pickle(file, compression=None)
        job.save()
        file.close()
        print("Caching {} for job {} begin!".format(featurizer, job_id))
        html = mark_safe(df.to_html(classes=['table', 'table-striped', 'table-bordered', 'text-nowrap']))
        cache.set(str(job_id) + "_" + choose_data + "_html_graph", html)
    else:
        print(df)
    job.status = 'I'
    job.save()
    print("Process {} for job {} finished!".format(featurizer, job_id))
