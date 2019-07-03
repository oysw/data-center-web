# Data center web
## Introduce
This is a web based AI application especially for chemistry.

## Install
### Download the program:

```
cd /path/to/workdir
git clone https://github.com/oysw/dsweb.git
```

### Install required package:

```
sudo apt install virtualenv python3-pip redis
virtualenv venv --python=python3
source venv/bin/activate
pip install -r requirements.txt
```

### Configure database

```
python manage.py migrate
```

### Start celery (New terminal)

```
celery worker -A dsweb -l info -c 1
```

### Start (Django debug option must be set to "True"):

```
python manage.py runserver
```

And you will reach the index page when you browse http://127.0.0.1:8000

## For persistent running (deployment)
1. Set django debug mode to false.
> Edit "dsweb/settings.py". Find the DEBUG option and set it to False.

2. Collect static file:

```
python manage.py collectstatic
```

3. Configure uwsgi
>Copy the uwsgi configuration template provided below to assigned path.
>
>Edit 'chdir', 'uid', 'gid' according to your OS.
>
>chdir: The path you install dsweb.
uid: The user you want to execute dsweb in your linux OS.
gid: The group of the user you selected above.
>
>For customization, visit uwsgi official doc website [here](https://uwsgi-docs.readthedocs.io/en/latest/).

4. Configure nginx
>Copy the nginx configuration template provided below to assigned path.
>
>Edit 'upstream django: server', 'server: location /static' according to your situation
>
>You can install nginx and dsweb in the same computer or not. So the address of upstream django server depends on where you install dsweb. If you install them in different computer, please copy the static file to where nginx is installed and assign the correct location of static file.
>
>If you want to customize nginx, refer to nginx official document [here](http://nginx.org/en/docs/).

5. Configure celery
>Copy the celery configuration template provided below to assigned path.
>
>Edit 'CELERY_BIN', 'CELERYD_PID_FILE', 'CELERYD_LOG_FILE' according to your situation
>
>Note that please create the directories you assign first, or service will fail to start.
>
>CELERY_BIN: path of celery excutable file.
CELERYD_PID_FILE: file for storing pid.
CELERYD_LOG_FILE: output file.
>
>For more information, visit celery doc [here](http://docs.celeryproject.org/en/latest/).

6. Start celery, uwsgi, nginx with systemd
>Script for each of above is provided below. If your system doesn't support systemd. You can choose another way. This step is to daemonize dsweb. You can also open three terminals for temporary usage.

### Script for Configuration

#### nginx
Path: /etc/nginx/sites-enabled/dsweb_nginx.conf
> nginx configuration file
```
# dsweb_nginx.conf

# the upstream component nginx needs to connect to
upstream django {
    # server unix:///path/to/your/mysite/mysite.sock; # for a file socket
    server *.*.*.*:8000; # for a web port socket
}

# configuration of the server
server{
    # the port your site will be served on
    listen 80;
    # the domain name it will serve for
    server_name 0.0.0.0; # substitute your machine's IP address or FQDN
    charset     utf-8;

    # max upload size
    client_max_body_size 128M;   # adjust to taste

    # Django media
    location /media  {
        alias /tmp/ai4chem;  # your Django project's media files - amend as required
    }

    location /static {
        alias /path/to/static; # your Django project's static files - amend as required
    }

    # Finally, send all non-media requests to the Django server.
    location / {
	uwsgi_read_timeout 600;
	uwsgi_pass  django;
        include     /etc/nginx/uwsgi_params; # the uwsgi_params file you installed
    }
}
```

#### uwsgi
Path: /etc/uwsgi/vassals/dsweb.ini
> uwsgi configuration file

```
[uwsgi]
socket=0.0.0.0:8000
chdir = /home/path/to/dsweb/
master=true
module=dsweb.wsgi
stats = 0.0.0.0:9191
uid=root (Edit this to the user you want)
gid=root (Edit this to the group you want)
```

Path: /etc/systemd/system/emperor.uwsgi.service
> manage uwsgi by systemd

```
[Unit]
Description=uWSGI Emperor
After=syslog.target

[Service]
ExecStart=/home/path/to/dsweb/venv/bin/uwsgi --emperor /etc/uwsgi/vassals
Restart=always
KillSignal=SIGQUIT
Type=notify
StandardError=syslog
NotifyAccess=all

[Install]
WantedBy=multi-user.target
```

#### celery
Path: /etc/celery/celery.conf
> celery configuration file

```
# Name of nodes to start
# here we have a single node
CELERYD_NODES="w1"
# or we could have three nodes:
# CELERYD_NODES="w1 w2 w3"

# Absolute or relative path to the 'celery' command:
# CELERY_BIN="/usr/local/bin/celery"
CELERY_BIN="/path/to/dsweb/venv/bin/celery"

# App instance to use
# comment out this line if you don't use an app
CELERY_APP="dsweb"
# or fully qualified:
# CELERY_APP="proj.tasks:app"

# How to call manage.py
CELERYD_MULTI="multi"

# Extra command-line arguments to the worker
CELERYD_OPTS="--concurrency=1"

# - %n will be replaced with the first part of the nodename.
# - %I will be replaced with the current child process index
#   and is important when using the prefork pool to avoid race conditions.
CELERYD_PID_FILE="/tmp/celery/%n.pid"
CELERYD_LOG_FILE="/tmp/celery/%n%I.log"
CELERYD_LOG_LEVEL="INFO"

# you may wish to add these options for Celery Beat
# CELERYBEAT_PID_FILE="/var/run/celery/beat.pid"
# CELERYBEAT_LOG_FILE="/var/log/celery/beat.log"

```

Path: /etc/systemd/system/celery.service
> manage celery by systemd

```
[Unit]
Description=Celery Service
After=network.target

[Service]
Type=forking
User=root (Edit this to the user you want)
Group=root (Edit this to the group you want)
EnvironmentFile=/etc/celery/celery.conf
WorkingDirectory=/path/to/dsweb
ExecStart=/bin/sh -c '${CELERY_BIN} multi start ${CELERYD_NODES} \
  -A ${CELERY_APP} --pidfile=${CELERYD_PID_FILE} \
  --logfile=${CELERYD_LOG_FILE} --loglevel=${CELERYD_LOG_LEVEL} ${CELERYD_OPTS}'
ExecStop=/bin/sh -c '${CELERY_BIN} multi stopwait ${CELERYD_NODES} \
  --pidfile=${CELERYD_PID_FILE}'
ExecReload=/bin/sh -c '${CELERY_BIN} multi restart ${CELERYD_NODES} \
  -A ${CELERY_APP} --pidfile=${CELERYD_PID_FILE} \
  --logfile=${CELERYD_LOG_FILE} --loglevel=${CELERYD_LOG_LEVEL} ${CELERYD_OPTS}'

[Install]
WantedBy=multi-user.target

```