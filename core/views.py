"""
Request handler.
"""
import pandas as pd
import joblib
import os
from io import BytesIO
from django.shortcuts import render
from django.contrib import auth
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.http import StreamingHttpResponse
from django.utils.safestring import mark_safe
from django.core.files import File

from django.utils.crypto import get_random_string
from core.models import Job
from core.tools import draw_pic
from core.pre_process import preprocess
from dsweb.settings import MEDIA_ROOT
# Create your views here.


def index(request):
    """
    Return the home page when the first visit.
    :param request:
    :return:
    """
    return render(request, 'index.html')


def login(request):
    """
    Handle login request.
    :param request:
    :return:
    """
    if 'username' in request.session.keys():
        return render(request, 'upload.html')
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        try:
            User.objects.get(username=username)
        except User.DoesNotExist:
            return render(request, 'login.html', {'error': 'No such user!'})
        user = authenticate(username=username, password=password)
        if user:
            auth.login(request, user)
            request.session['username'] = username
            return render(request, 'upload.html')
        else:
            return render(request, 'login.html', {'error': 'Incorrect password'})
    else:
        return render(request, 'login.html')


def register(request):
    """
    Handle register request.
    :param request:
    :return:
    """
    if request.method == 'POST':
        username = request.POST['username']
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


def upload(request):
    """
    Get the uploaded file and switch to preprocess page
    :param request:
    :return:
    """
    if request.method == "POST":
        file = request.FILES.get('file')
        if file is None:
            return render(request, 'upload.html', {'error': 'Please choose a file!'})
        status, df = preprocess([], file)
    else:
        option = request.GET
        option = list(option)
        job_id = request.session["job_id"]
        status, df = preprocess(option, Job.objects.get(id=job_id).data)
    if status:
        f = File(BytesIO())
        df.to_pickle(f, compression=None)
        try:
            job_id = request.session["job_id"]
            file_path = request.session["job_file_path"]
            try:
                os.remove(MEDIA_ROOT + file_path)
            except FileNotFoundError:
                pass
            job = Job.objects.get(id=job_id)
            f.name = file_path.split("/")[-1]
            job.data = f
            job.save()
            job.data.close()
        except KeyError:
            f.name = get_random_string(7) + '.pkl'
            job = Job.objects.create(
                owner=request.session['username'],
                data=f
            )
            job_id = job.id
            request.session["job_id"] = job_id
            request.session["job_file_path"] = job.data.name
            job.data.close()
        return_dict = {
            'html': mark_safe(df.to_html()),
            'job_id': job_id
        }
        if request.method == "POST":
            return render(request, 'upload.html', return_dict)
        else:
            return JsonResponse(return_dict)
    else:
        if request.method == "POST":
            return render(request, 'upload.html', {'error': df})
        else:
            return JsonResponse({'error': df})


def submit(request):
    """
    Submit the job and begin calculating
    :param request:
    :return:
    """
    job_id = request.session["job_id"]
    job = Job.objects.get(id=job_id)
    job.status = "W"
    job.save()
    try:
        del request.session["job_id"]
        del request.session["job_file_path"]
    except KeyError:
        pass
    return render(request, "upload.html")


def logout(request):
    """
    Delete the username in the session.
    :param request:
    :return:
    """
    try:
        del request.session['username']
        del request.session['job_id']
        del request.session["job_file_path"]
    except KeyError:
        pass
    return render(request, 'index.html')


def result(request):
    """
    Switch to result page.
    :param request:
    :return:
    """
    if 'username' in request.session.keys():
        return render(request, 'result.html', {'result': get_result(request.session['username'])})
    else:
        return render(request, "index.html")


def draw(request):
    """
    Graph making entrance point.
    :param request:
    :return:
    """
    if request.is_ajax():
        if request.method == "POST":
            pic, err, file = draw_pic(request)
            return JsonResponse({"image": pic, "err": err, "file": file})


def data_detail(request):
    """
    Analyze uploaded new dataset and return the shape of new dataset.
    :param request:
    :return:
    """
    if request.method == "GET":
        data = request.GET
        model_id = int(data["model_id"])
        try:
            job = Job.objects.get(id=model_id)
        except Job.DoesNotExist:
            return JsonResponse({"label": ""})
        data = pd.read_pickle(job.data)
        job.data.close()
        return JsonResponse({"label": list(data.columns)})

    if request.method == "POST":
        file = request.FILES.get("test")
        status, df = preprocess([], file)
        if status:
            data = df
        else:
            return JsonResponse({"label": ""})
        return JsonResponse({"label": list(data.columns)})


def get_result(username):
    """
    Create the result list on the result page.
    :param username:
    :return:
    """
    jobs = Job.objects.filter(owner=username, status='F')
    for job in jobs:
        # Model
        try:
            mod = job.mod.file
            mod = joblib.load(mod)
            job.mod = mod.__class__.__name__
        except FileNotFoundError:
            job.mod = ''
    return jobs


def download_predict(request):
    """
    Provide predict file.
    :param request:
    :return:
    """
    file_name = request.GET["file"] + ".txt"
    file_path = MEDIA_ROOT + 'predict/' + file_name

    def yield_file(file_n):
        """
        Create the content of the file.
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
