"""
Request handler.
"""
import pandas as pd
import joblib
import os
from io import BytesIO
from django.shortcuts import render, redirect
from django.contrib import auth
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.http import StreamingHttpResponse
from django.utils.safestring import mark_safe
from django.core.files import File
from django.contrib.auth.decorators import login_required
from core.tools import username_check
from django.utils.crypto import get_random_string
from core.models import Job
from core.tools import draw_pic
from core.pre_process import preprocess
from dsweb.settings import MEDIA_ROOT
# Create your views here.


def index(request):
    """
    :param request:
    :return:
    """
    return render(request, 'index.html')


def login(request):
    """
    :param request:
    :return:
    """
    if 'username' in request.session.keys():
        return home(request)
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        try:
            User.objects.get(username=username)
        except User.DoesNotExist:
            return render(request, 'login.html', {'error': 'No such user!'})
        user = auth.authenticate(username=username, password=password)
        if user:
            auth.login(request, user)
            request.session['username'] = username
            return home(request)
        else:
            return render(request, 'login.html', {'error': 'Incorrect password'})
    else:
        return render(request, 'login.html')


def register(request):
    """
    :param request:
    :return:
    """
    if request.method == 'POST':
        username = request.POST['username']
        if not username_check(username):
            format_err = 'Username should only contain numbers, letters and underlines, ' \
                         'and start with letters'
            return render(request, 'register.html', {'name_error': format_err})
        password = request.POST['password']
        if username == '':
            return render(request, 'register.html', {'name_error': 'Please enter username!'})
        if password == '':
            return render(request, 'register.html', {'pass_error': 'please enter password!', 'username': username})
        try:
            User.objects.get(username=username)
        except User.DoesNotExist:
            User.objects.create_user(username=username, password=password)
            try:
                del request.session['username']
            except KeyError:
                pass
            return render(request, 'login.html')
        return render(request, 'register.html', {'name_error': 'User already exists!'})
    else:
        return render(request, 'register.html')


@login_required
def logout(request):
    """
    :param request:
    :return:
    """
    auth.logout(request)
    return redirect('/')


@login_required
def home(request):
    """
    Jump to home page.
    :param request:
    :return:
    """
    username = request.session['username']
    jobs = Job.objects.filter(owner=username)
    for job in jobs:
        try:
            best = joblib.load(job.mod)
            job.mod = best.__class__.__name__
        except ValueError:
            pass
    return_dict = {'username': username, 'jobs': jobs}
    return render(request, 'home.html', return_dict)


@login_required
def add_new_job(request):
    """
    :param request:
    :return:
    """
    username = request.session['username']
    label = request.POST['label']
    Job.objects.create(owner=username, label=label)
    return home(request)


@login_required
def delete_job(request):
    """
    :param request:
    :return:
    """
    job_id = request.GET['job_id']
    try:
        Job.objects.get(id=job_id).delete()
    except Job.DoesNotExist:
        pass
    return home(request)


@login_required
def upload_page(request):
    file_info = {
        'job_id': request.GET['job_id'],
        'choose_data': request.GET['choose_data']
    }
    return render(request, 'upload.html', file_info)


@login_required
def upload(request):
    file = request.FILES.get('file')
    try:
        job_id = int(request.POST['job_id'])
        choose_data = request.POST['choose_data']
    except Exception as e:
        print(e)
        return home(request)
    return_dict = {
        'job_id': job_id,
        'choose_data': choose_data,
    }
    if file is None:
        return_dict['error'] = 'Please choose a file!'
        return render(request, 'upload.html', return_dict)
    job = Job.objects.get(id=job_id)
    status, df = preprocess([], file)
    if status:
        file = File(BytesIO())
        df.to_pickle(file, compression=None)
        file.name = get_random_string(7) + '.pkl'
    else:
        return_dict['error'] = df
        return render(request, 'upload.html', return_dict)
    if choose_data == 'raw':
        job.raw = file
    elif choose_data == 'upload':
        job.upload = file
    else:
        return_dict['error'] = 'Unexpect error!'
        return render(request, 'upload.html', return_dict)
    job.save()
    return home(request)


@login_required
def process_page(request):
    job_id = int(request.GET['job_id'])
    choose_data = request.GET['choose_data']
    job = Job.objects.get(id=job_id)
    if choose_data == 'raw':
        status, df = preprocess([], job.raw)
    elif choose_data == 'upload':
        status, df = preprocess([], job.upload)
    else:
        return render(request, 'process.html')
    return_dict = {
        'job_id': job_id,
        'choose_data': choose_data,
        'html': mark_safe(df.to_html())
    }
    return render(request, 'process.html', return_dict)


@login_required
def process(request):
    featurizer = request.GET["featurizer"]
    target = request.GET["target_column"]
    try:
        value = request.GET["value"]
    except KeyError:
        value = ""
    option = [featurizer, target, value]
    job_id = int(request.GET["job_id"])
    job = Job.objects.get(id=job_id)
    if request.GET['choose_data'] == 'raw':
        file = job.raw
    elif request.GET['choose_data'] == 'upload':
        file = job.upload
    else:
        return JsonResponse({'error': ""})
    status, df = preprocess(option, file)
    """
    If the process of data succeeds without error reports, save new data in database.
    """
    if status:
        file.open('wb')
        file.truncate()
        file.seek(0)
        df.to_pickle(file, compression=None)
        job.save()
        file.close()
        return_dict = {
            'html': mark_safe(df.to_html()),
        }
        return JsonResponse(return_dict)
    else:
        return JsonResponse({'error': df})


@login_required
def submit_page(request):
    job_id = request.GET['job_id']
    job_id = int(job_id)
    job = Job.objects.get(id=job_id)
    file = job.raw
    df = pd.read_pickle(file, compression=None)
    file.close()
    columns = list(df.columns)
    return_dict = {
        'job_id': job_id,
        'columns': columns
    }
    return render(request, 'confirm.html', return_dict)


@login_required
def submit(request):
    """
    Submit the job and begin calculating
    :param request:
    :return:
    """
    job_id = int(request.POST["job_id"])
    # Remove csrf item.
    target = request.POST['columnAsTarget']
    columns = list(request.POST)[2:-1]
    job = Job.objects.get(id=job_id)
    file = job.raw
    df = pd.read_pickle(file, compression=None)
    file.close()
    if target not in columns:
        columns.append(target)
    else:
        columns.append(columns.pop(columns.index(target)))
    df = df[columns]
    file.open("wb")
    file.truncate()
    file.seek(0)
    df.to_pickle(file, compression=None)
    file.close()
    job.status = "W"
    job.save()
    return home(request)


@login_required
def draw_page(request):
    """
    :param request:
    :return:
    """
    job_id = int(request.GET["job_id"])
    choose_data = request.GET["choose_data"]
    job = Job.objects.get(id=job_id)
    status, raw_df = preprocess([], job.raw)
    if not status:
        return render(request, "draw.html", {"error": raw_df})
    return_dict = {
        'job_id': job_id,
        'choose_data': choose_data,
        'raw_columns': list(raw_df.columns)[:-1]
    }
    if choose_data == 'upload':
        status, upload_df = preprocess([], job.upload)
        if not status:
            return render(request, "draw.html", {"error": upload_df})
        return_dict['upload_columns'] = list(upload_df.columns)
    return render(request, "draw.html", return_dict)


@login_required
def draw(request):
    if request.method == 'POST':
        option = request.POST
        html, error = draw_pic(option)
        if error != "":
            return JsonResponse({"err": error})
        else:
            return JsonResponse({"image": html, "err": ""})
    else:
        return home(request)


@login_required
def download_predict(request):
    """
    Predict data are saved in directory /tmp/ai4chem/predict/.
    :param request:
    :return:
    """
    file_name = request.session["username"] + ".txt"
    file_path = MEDIA_ROOT + 'predict/' + file_name

    def yield_file(file_n):
        """
        Transported by stream.
        :param file_n:
        :return:
        """
        chunk_size = 512
        with open(file_n, 'r') as _f:
            while True:
                content = _f.read(chunk_size)
                if content:
                    yield content
                else:
                    break
    response = StreamingHttpResponse(yield_file(file_path))
    response['Content-Type'] = 'application/octet-stream'
    response['Content-Disposition'] = 'attachment;filename="{}"'.format(file_name)
    return response
