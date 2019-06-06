"""
Tool used to maintain the program.
"""
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
from dsweb.settings import MEDIA_ROOT
from . import post_process


def draw_pic(request):
    """
    load data and assign plotting task
    :param request:
    :return:
    """
    option = request.POST
    model_id = int(option["id"])
    job = Job.objects.get(id=model_id)
    data = pd.read_pickle(job.data, compression=None)
    x = data[data.columns[0: -1]]
    y = data[data.columns[-1]]
    mod = joblib.load(job.mod.file)

    if option["chooseData"] == 'raw':
        x_test = x
        y_pred = mod.predict(x_test)

    elif option["chooseData"] == 'upload':
        file = MEDIA_ROOT + request.session["username"]
        try:
            x_test = pd.read_pickle(file, compression=None)
        except Exception as _e:
            print(_e)
            return "", "Uploaded file is invalid.", ""
        try:
            plot_columns = []
            for key in option:
                if option[key] == "on":
                    plot_columns.append(key)
            x_test = x_test[plot_columns]
            y_pred = mod.predict(x_test)
        except ValueError as _e:
            return "", "Uploaded file is unacceptable or mismatches the shape of raw data.", ""
    else:
        return "", "Please choose a data type", ""

    file_name = post_process.predict_file_create(y_pred)

    try:
        f1 = option["feature_1"]
        f2 = option["feature_2"]
    except Exception as e:
        print(e)
        f1 = f2 = "0"
        pass
    if f1 != '0' and f2 != '0':
        return draw_pic_3d(option, x, y, x_test, y_pred), "", file_name
    elif f1 != '0' or f2 != '0':
        return draw_pic_2d(option, x, y, x_test, y_pred), "", file_name
    else:
        return "", "Please choose feature!", ""


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
    if option["feature_1"] != '0':
        plot_feature = option["feature_1"]
    else:
        plot_feature = option["feature_2"]
    index = list(x_test.columns).index(plot_feature)
    x_test = x_test[plot_feature]
    x = x[list(x.columns)[index]]

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
    plot_feature_1 = option["feature_1"]
    plot_feature_2 = option["feature_2"]
    index_1 = list(x_test.columns).index(plot_feature_1)
    index_2 = list(x_test.columns).index(plot_feature_2)
    x_test_1 = x_test[plot_feature_1]
    x_test_2 = x_test[plot_feature_2]
    x_1 = x[list(x.columns)[index_1]]
    x_2 = x[list(x.columns)[index_2]]

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
    if not is_last_job_finished():
        return
    save_current_job_id(os.getpid())
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


def is_last_job_finished():
    if not os.path.exists('/tmp/ai4chem/script/ds_current_job.txt'):
        return True
    with open('/tmp/ai4chem/script/ds_current_job.txt', 'r') as f:
        pid = f.read()
    if psutil.pid_exists(eval(pid)):
        return False
    else:
        return True


def save_current_job_id(pid):
    if not os.path.exists('/tmp/ai4chem/script/'):
        os.makedirs('/tmp/ai4chem/script/')
    with open('/tmp/ai4chem/script/ds_current_job.txt', 'w') as f:
        f.write(str(pid))
    return


def job_error(job, e):
    job.status = 'E'
    print(e)
    job.save()
    os.remove('/tmp/ai4chem/script/ds_current_job.txt')
    return
