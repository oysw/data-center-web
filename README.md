﻿﻿# Data center web## IntroduceThis is a web based AI application especially for chemistry.## InstallDownload the program:```cd /path/to/workdirgit clone https://github.com/oysw/dsweb.git```Install required package:```sudo apt install virtualenv python3-pip mysql-server-5.7 libmysqlclient-devvirtualenv venv --python=python3source venv/bin/activatepip install -r requirements.txt```Collect static file:```python manage.py collectstatic```Configure dsweb:>You can find the uwsgi configure file (dsweb.ini) in root directory of dsweb.```[uwsgi]http = 0.0.0.0:8000chdir = /home/path/to/dsweb/# wsgi-file = dsweb/wsgi.pymaster=truemodule=dsweb.wsgistats = 0.0.0.0:9191static-map = /static/=static/```Change the `chdir` to the directory where you downloaded dsweb.Simply run:```uwsgi dsweb.ini```And you will reach the index page when you browse http://127.0.0.1:8000## (Recommended)If your linux system boots with systemd, you can start dsweb by systemd.Copy the `dsweb.ini` to this place:```sudo mkdir -p /etc/uwsgi/vassals/sudo cp dsweb.ini /etc/uwsgi/vassals/```You can add a configure file in this place:```sudo vim /etc/systemd/system/emperor.uwsgi.service```The file may  look like this:```[Unit]Description=uWSGI EmperorAfter=syslog.target[Service]ExecStart=/home/path/to/dsweb/venv/bin/uwsgi --emperor /etc/uwsgi/vassalsRestart=alwaysKillSignal=SIGQUITType=notifyStandardError=syslogNotifyAccess=all[Install]WantedBy=multi-user.target```Where the `ExecStart` is the path of uwsgi.>If you don't know where it is, just type >```>whereis uwsgi>```Then start dsweb by:```sudo service emperor.uwsgi start```