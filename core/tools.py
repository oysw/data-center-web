import re
import os
import paramiko
import base64
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
from sklearn.externals import joblib
from dsweb.settings import DATA_CENTER
from dsweb.settings import MEDIA_ROOT
from core.models import Job


def upload_to_center():
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
    local_file = MEDIA_ROOT + "result/"
    remote_file = MEDIA_ROOT + "result/"
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(**DATA_CENTER)
    stdin, stdout, stderr = ssh.exec_command('ls ' + remote_file)
    if stdout.read().decode('utf-8') == "":
        return
    try:
        os.makedirs(local_file)
    except FileExistsError:
        pass
    remote_file_list = stdout.read().decode('utf-8').rstrip("\n").split("\n")
    paramiko.SFTPClient.from_transport(ssh.get_transport())
    sftp = ssh.open_sftp()
    for f in remote_file_list:
        sftp.get(os.path.join(remote_file, f), os.path.join(local_file, f))
    ssh.close()
    return


def del_file(path):
    local_file_list = os.listdir(path)
    for f in local_file_list:
        f_path = os.path.join(path, f)
        if os.path.isdir(f_path):
            del_file(f_path)
            os.rmdir(f_path)
        else:
            os.remove(f_path)


def draw_pic(option):
    model_id = option["id"]
    job = Job.objects.get(id=model_id)
    mod = joblib.load(job.mod.file)

    x_test = np.load(job.x_file.file)
    y_pred = mod.predict(x_test)

    plt.figure()
    plt.title(option["title"])
    plt.xlabel(option["x_label"])
    plt.ylabel(option["y_label"])
    plt.scatter(x_test, y_pred, c=option["predict_color"])

    buffer = BytesIO()
    plt.savefig(buffer)
    img = buffer.getvalue()
    imb = base64.b64encode(img)
    ims = imb.decode()
    imd = "data:image/png;base64," + ims
    return imd
