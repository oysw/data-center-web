"""
Request handler.
"""
import pandas as pd
import joblib
from django.shortcuts import render
from django.contrib import auth
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.http import StreamingHttpResponse
from django.utils.safestring import mark_safe

from django.utils.crypto import get_random_string
from core.models import Job
from core.tools import draw_pic
from core.tools import csv_check
from core.pre_process import csv_preprocess
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


def preprocess(request):
    """
    preprocess csv and add some chemical feature
    :param request:
    :return:
    """
    return 0


def upload(request):
    """
    Get the uploaded file and switch to preprocess page
    :param request:
    :return:
    """
    csv_file = request.FILES.get('file')
    if csv_file is None:
        return render(request, 'upload.html', {'error': 'Please choose a file!'})
    if not csv_check(csv_file):
        return render(request, 'upload.html', {'error': 'File is not csv format!'})
    status, csv_html = csv_preprocess([], csv_file)

    if status:
        return render(request, 'preprocess.html', {'html': mark_safe(csv_html)})
    else:
        return render(request, 'upload.html', {'error': csv_html})


def submit(request):
    """
    Upload the file to data center and save them to the database.
    Because this program is designed as Web-compute mode, at the end of this function, there /
    will be a transportation action.
    :return:
    """
    # csv_file.name = 'csv_' + get_random_string(7) + '.csv'
    # Job.objects.create(
    #     owner=request.session['username'],
    #     csv_data=csv_file
    # )
    return 0


def logout(request):
    """
    Delete the username in the session.
    :param request:
    :return:
    """
    try:
        del request.session['username']
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
        data = pd.read_csv(job.csv_data)
        return JsonResponse({"label": list(data.columns)})

    if request.method == "POST":
        file = request.FILES.get("test")
        if not csv_check(file):
            JsonResponse({"label": ""})
        data = pd.read_csv(file)
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
