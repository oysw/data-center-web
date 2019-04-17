import re
import os
import paramiko
from dsweb.settings import DATA_CENTER
from dsweb.settings import MEDIA_ROOT


def upload_to_center():
    local_file = MEDIA_ROOT
    remote_file = MEDIA_ROOT
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(**DATA_CENTER)
    stdin, stdout, stderr = ssh.exec_command('ls ' + remote_file)
    # The first-time upload
    err = stderr.read().decode('utf-8')
    pattern = re.compile("No such file or directory")
    if re.search(pattern, err):
        stdin, stdout, stderr = ssh.exec_command('mkdir -p ' + remote_file)
        if stderr.read.decode('utf-8') != '':
            return
    paramiko.SFTPClient.from_transport(ssh.get_transport())
    sftp = ssh.open_sftp()
    for f in os.listdir(local_file):
        sftp.put(os.path.join(local_file, f), os.path.join(remote_file, f))
    ssh.close()
#    del_file(local_file)
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
