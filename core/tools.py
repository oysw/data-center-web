"""
Tool used to maintain the program.
"""
import re
import os
import psutil
import pandas as pd
from core.models import Job
import plotly.offline as of
import plotly.graph_objs as go
from io import BytesIO
import joblib
from core.automl.auto_ml import auto_ml
from django.core.files import File
from django.utils.crypto import get_random_string
from django.core.cache import cache
from . import post_process


def username_check(username):
    """
    Valid username contains only letters, numbers and underlines.
    And only start with letters.
    :param username:
    :return: True or false
    """
    num_letter = re.compile(r"^(?!\d+$)[\da-zA-Z_]+$")
    first_letter = re.compile(r"^[a-zA-Z]")
    if first_letter.search(username):
        if num_letter.search(username):
            return True
    return False


def draw_pic(option):
    job_id = int(option["job_id"])
    job = Job.objects.get(id=job_id)
    data = pd.read_pickle(job.raw, compression=None)
    x = data[data.columns[0: -1]]
    y = data[data.columns[-1]]
    mod = joblib.load(job.mod)

    # Plot with raw data(Training data)
    if option["choose_data"] == 'raw':
        x_test = x
        y_pred = mod.predict(x_test)

    # Plot with uploaded new data.
    elif option["choose_data"] == 'upload':
        file = job.upload
        try:
            x_test = pd.read_pickle(file, compression=None)
        except Exception as _e:
            print(_e)
            return "", "Uploaded file is invalid."
        try:
            """
            Not all the columns could be used for prediction. Only pure numbers is acceptable.
            Even though there are restrictions on front-end page, possible flaws may occur.
            """
            plot_columns = []
            for key in option:
                if option[key] == "on":
                    plot_columns.append(key)
            x_test = x_test[plot_columns]
            y_pred = mod.predict(x_test)
        except ValueError as _e:
            return "", "Uploaded file is unacceptable or mismatches the shape of raw data."
    else:
        return "", "Please choose a data type"

    post_process.predict_file_create(y_pred, job.owner)

    try:
        # Select columns need to be plotted.
        f1 = option["feature_1"]
        f2 = option["feature_2"]
    except Exception as e:
        print(e)
        f1 = f2 = "0"
        pass
    if f1 != 'None' and f2 != 'None':
        return draw_pic_3d(option, x, y, x_test, y_pred), ""
    elif f1 != 'None' or f2 != 'None':
        return draw_pic_2d(option, x, y, x_test, y_pred), ""
    else:
        return "", "Please choose feature!"


def draw_pic_2d(option, x, y, x_test, y_pred):
    """
    plot 2d graph
    :param option: graph option
    :param x: x_axis value(raw)
    :param y: y_axis value(raw)
    :param x_test: x_axis value(provided or raw)
    :param y_pred: y_axis value(calculated)
    :return:
    """
    if option["feature_1"] != 'None':
        plot_feature = int(option["feature_1"])
    else:
        plot_feature = int(option["feature_2"])
    x_test = x_test[x_test.columns[plot_feature]]
    x = x[x.columns[plot_feature]]

    trace_raw = go.Scatter(
        x=x,
        y=y,
        name='raw',
        mode='markers',
        marker=dict(
            size=10,
            color=option["raw_color"]
        )
    )
    trace_pred = go.Scatter(
        x=x_test,
        y=y_pred,
        name='predict',
        mode='markers',
        marker=dict(
            size=5,
            color=option["predict_color"]
        )
    )

    layout = go.Layout(
        title=option["title"],
        xaxis=dict(title=x_test.name),
        yaxis=dict(title=y.name)
    )
    data = [trace_raw, trace_pred]
    fig = dict(data=data, layout=layout)
    html = of.plot(fig, output_type="div")
    return html


def draw_pic_3d(option, x, y, x_test, y_pred):
    """
    plot 3d graph
    :param option:
    :param x:
    :param y:
    :param x_test:
    :param y_pred:
    :return:
    """
    plot_feature_1 = int(option["feature_1"])
    plot_feature_2 = int(option["feature_2"])
    x_test_1 = x_test[x_test.columns[plot_feature_1]]
    x_test_2 = x_test[x_test.columns[plot_feature_2]]
    x_1 = x[x.columns[plot_feature_1]]
    x_2 = x[x.columns[plot_feature_2]]

    trace_raw = go.Scatter3d(
        x=x_1,
        y=x_2,
        z=y,
        name='raw',
        mode='markers',
        marker=dict(
            size=10,
            color=option["raw_color"]
        )
    )
    trace_pred = go.Scatter3d(
        x=x_test_1,
        y=x_test_2,
        z=y_pred,
        name='predict',
        mode='markers',
        marker=dict(
            size=5,
            color=option["predict_color"]
        )
    )

    layout = go.Layout(
        title=option["title"],
        scene=go.Scene(
            xaxis=go.layout.scene.XAxis(
                title=x_test_1.name,
                showbackground=True,
                backgroundcolor='rgb(230, 230, 230)'
            ),
            yaxis=go.layout.scene.YAxis(
                title=x_test_2.name,
                showbackground=True,
                backgroundcolor='rgb(230, 230, 230)'
            ),
            zaxis=go.layout.scene.ZAxis(
                title=y.name,
                showbackground=True,
                backgroundcolor='rgb(230, 230, 230)'
            )
        )
    )

    data = [trace_raw, trace_pred]
    fig = dict(data=data, layout=layout)
    html = of.plot(fig, output_type="div")
    return html


def calculate():
    """
    This function is scheduled to work every minutes. Powered by crontab in Linux system.
    It doesn't work in Windows system.
    Analyze the data and save the machine learning models provided by sklearn.
    Currently involved models:
        Regression：
            Linear, Nearest Neighbour, Random Forests, Support Vectors Machine, Multiple Layers Perception.
        Classification:
            None
    :return:
    """
    calculate_pid = cache.get("calculating_process_id")
    if calculate_pid is not None:
        if psutil.pid_exists(calculate_pid):
            return
    cache.set("calculating_process_id", os.getpid(), timeout=None)
    job_list = Job.objects.filter(status='W').order_by('create_time')
    if len(job_list) == 0:
        return
    job = job_list.first()
    try:
        data = pd.read_pickle(job.data, compression=None)
    except Exception as e:
        job_error(job, e)
        return
    job.status = 'C'
    job.save()
    try:
        x = data[data.columns[0: -1]]
        y = data[data.columns[-1]]
        mod = auto_ml(x, y)
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


def job_error(job, e):
    """
    Used for error processing.
    Switch the status of job to Error!
    :param job:
    :param e:
    :return:
    """
    job.status = 'E'
    print(e)
    job.save()
    os.remove('/tmp/ai4chem/script/ds_current_job.txt')
    return
