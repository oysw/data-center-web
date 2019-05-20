'''
Tool used to maintain the program.
'''
import re
import os
import base64
from io import BytesIO
import paramiko
import joblib
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from dsweb.settings import DATA_CENTER
from dsweb.settings import MEDIA_ROOT
from core.models import Job

from . import post_process


def upload_to_center():
    '''
    upload files to dslocal everytime new job submit.
    '''
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


def download_to_web():
    '''
    download model when browsing result page.
    '''
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
    '''
    delete dir
    '''
    local_file_list = os.listdir(path)
    for f in local_file_list:
        f_path = os.path.join(path, f)
        if os.path.isdir(f_path):
            del_file(f_path)
            os.rmdir(f_path)
        else:
            os.remove(f_path)


def draw_pic(request):
    '''
    load data and assign plotting task
    '''
    option = request.POST
    print(option)
    model_id = option["id"]
    job = Job.objects.get(id=model_id)
    x = np.load(job.x_file.file)
    y = np.load(job.y_file.file)
    mod = joblib.load(job.mod.file)

    if option["chooseData"] == '1':
        x_test = x
        y_pred = mod.predict(x_test)

    elif option["chooseData"] == '2':
        file = request.FILES.get("x_test")
        try:
            x_test = np.load(file)
        except TypeError:
            return "", "Please upload a file", ""
        try:
            y_pred = mod.predict(x_test)
        except ValueError as _e:
            return "", _e.args[0], ""
    else:
        x_test = x
        y_pred = y

    file_name = post_process.predict_file_create(y_pred)

    if option["featureNum"] == '1':
        return draw_pic_2d(option, x, y, x_test, y_pred), "", file_name
    elif option["featureNum"] == '2':
        return draw_pic_3d(option, x, y, x_test, y_pred), "", file_name
    else:
        return "", "Please choose featureNum!", ""


def draw_pic_2d(option, x, y, x_test, y_pred):
    '''
    plot 2d graph
    '''
    x_test = x_test[:, int(option["feature_1"]) - 1].reshape(-1, 1)
    x = x[:, int(option["feature_1"]) - 1].reshape(-1, 1)

    plt.figure()
    plt.grid(True)
    plt.title(option["title"])
    plt.xlabel(option["x_label"])
    plt.ylabel(option["y_label"])
    if option['raw_color'] != 'none':
        plt.scatter(x, y, c=option["raw_color"], s=40, marker="^")
    if option['predict_color'] != 'none':
        plt.scatter(x_test, y_pred, c=option["predict_color"], s=10, marker="*")

    buffer = BytesIO()
    plt.savefig(buffer)
    img = buffer.getvalue()
    imb = base64.b64encode(img)
    ims = imb.decode()
    imd = "data:image/png;base64," + ims
    return imd


def draw_pic_3d(option, x, y, x_test, y_pred):
    '''
    plot 3d graph
    '''
    x_test_1 = x_test[:, int(option["feature_1"]) - 1].reshape(-1, 1)
    x_test_2 = x_test[:, int(option["feature_2"]) - 1].reshape(-1, 1)
    x_1 = x[:, int(option["feature_1"]) - 1].reshape(-1, 1)
    x_2 = x[:, int(option["feature_2"]) - 1].reshape(-1, 1)

    fig = plt.figure()
    ax = Axes3D(fig)
    ax.set_title(option["title"])
    if option['raw_color'] != 'none':
        ax.scatter(x_1, x_2, y, c=option["raw_color"], s=40)
    if option['predict_color'] != 'none':
        ax.scatter(x_test_1, x_test_2, y_pred, c=option["predict_color"], s=10)

    buffer = BytesIO()
    plt.savefig(buffer)
    img = buffer.getvalue()
    imb = base64.b64encode(img)
    ims = imb.decode()
    imd = "data:image/png;base64," + ims
    return imd
