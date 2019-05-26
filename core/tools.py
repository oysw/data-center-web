"""
Tool used to maintain the program.
"""
import re
import os
import paramiko
import joblib
import pandas as pd
from dsweb.settings import DATA_CENTER
from dsweb.settings import MEDIA_ROOT
from core.models import Job
import plotly.offline as of
import plotly.graph_objs as go

from . import post_process


def upload_to_center():
    """
    upload files to dslocal everytime new job submit.
    :return: No return value
    """
    local_file = MEDIA_ROOT + "raw/"
    remote_file = MEDIA_ROOT + "raw/"
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(**DATA_CENTER)
    stdin, stdout, stderr = ssh.exec_command('ls ' + remote_file)
    # The first-time upload
    err = stderr.read().decode('utf-8')
    pattern = re.compile("No such file or directory")
    if re.search(pattern, err):
        stdin, stdout, stderr = ssh.exec_command('mkdir -p ' + remote_file)
        if stderr.read().decode('utf-8') != '':
            return
    paramiko.SFTPClient.from_transport(ssh.get_transport())
    sftp = ssh.open_sftp()
    for f in os.listdir(local_file):
        sftp.put(os.path.join(local_file, f), os.path.join(remote_file, f))
    ssh.close()
#    del_file(local_file)
    return


def csv_check(file):
    """
    check if a file is csv, but maybe xyz file will pass
    :param file:
    :return:
    """
    suffix = file.name.split(".")[-1]
    if suffix != "csv":
        return False
    try:
        pd.read_csv(file)
        file.seek(0)
        return True
    except Exception as e:
        print(e)
        return False


def download_to_web():
    """
    download model when browsing result page.
    :return:
    """
    local_file = MEDIA_ROOT + "result/"
    remote_file = MEDIA_ROOT + "result/"
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(**DATA_CENTER)
    stdin, stdout, stderr = ssh.exec_command('ls ' + remote_file)
    file_list = stdout.read().decode('utf-8')
    if file_list == "":
        return
    try:
        os.makedirs(local_file)
    except FileExistsError:
        pass
    remote_file_list = file_list.rstrip("\n").split("\n")
    paramiko.SFTPClient.from_transport(ssh.get_transport())
    sftp = ssh.open_sftp()
    for f in remote_file_list:
        sftp.get(os.path.join(remote_file, f), os.path.join(local_file, f))
    ssh.close()
    return


def del_file(path):
    """
    delete dir
    :param path:
    :return:
    """
    local_file_list = os.listdir(path)
    for f in local_file_list:
        f_path = os.path.join(path, f)
        if os.path.isdir(f_path):
            del_file(f_path)
            os.rmdir(f_path)
        else:
            os.remove(f_path)


def draw_pic(request):
    """
    load data and assign plotting task
    :param request:
    :return:
    """
    option = request.POST
    model_id = option["id"]
    job = Job.objects.get(id=model_id)
    data = pd.read_csv(job.csv_data)
    x = data[data.columns[0: -1]]
    y = data[data.columns[-1]]
    mod = joblib.load(job.mod.file)

    if option["chooseData"] == '1':
        x_test = x
        y_pred = mod.predict(x_test)

    elif option["chooseData"] == '2':
        file = request.FILES.get("test")
        try:
            x_test = pd.read_csv(file)
        except Exception as _e:
            print(_e)
            return "", "Uploaded file is invalid.", ""
        try:
            y_pred = mod.predict(x_test)
        except ValueError as _e:
            return "", "Uploaded file is unacceptable.", ""
    else:
        return "", "Please choose a data type", ""

    file_name = post_process.predict_file_create(y_pred)

    f1 = option["feature_1"]
    f2 = option["feature_2"]
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
        plot_feature = int(option["feature_1"]) - 1
    else:
        plot_feature = int(option["feature_2"]) - 1
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
    plot_feature_1 = int(option["feature_1"]) - 1
    plot_feature_2 = int(option["feature_2"]) - 1
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
            size=5,
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
