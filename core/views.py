'''
Request handler.
'''
import numpy as np
import joblib
from django.shortcuts import render
from django.contrib import auth
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.http import StreamingHttpResponse

from django.utils.crypto import get_random_string
from core.models import Job
from core.tools import draw_pic
from core.tools import upload_to_center
from core.tools import download_to_web
from dsweb.settings import MEDIA_ROOT
# Create your views here.


def index(request):
    '''
    Return the home page when the first visit.
    '''
    return render(request, 'index.html')


def login(request):
    '''
    Handle login request.
    '''
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
    '''
    Handle register request.
    '''
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
    '''
    Get the uploaded file and save them to the database.
    Because this program is designed as Web-compute mode, at the end of this function, there /
    will be a transportation action.
    '''
    x_file = request.FILES.get('x_file')
    y_file = request.FILES.get('y_file')
    if x_file is None:
        return render(request, 'upload.html', {'x_error': 'Please choose a file!'})
    if y_file is None:
        return render(request, 'upload.html', {'y_error': 'Please choose a file!'})
    x_file.name = 'x_' + get_random_string(7) + '.npy'
    y_file.name = 'y_' + get_random_string(7) + '.npy'
    Job.objects.create(
        owner=request.session['username'],
        x_file=x_file,
        y_file=y_file,
    )
    upload_to_center()
    return render(request, 'upload.html', {'success': 'Job submits successfully!'})


def logout(request):
    '''
    Delete the username in the session.
    '''
    try:
        del request.session['username']
    except KeyError:
        pass
    return render(request, 'index.html')


def result(request):
    '''
    Switch to result page.
    '''
    if 'username' in request.session.keys():
        return render(request, 'result.html', {'result': get_result(request.session['username'])})
    else:
        return render(request, "index.html")


def draw(request):
    '''
    Graph making entrance point.
    '''
    if request.is_ajax():
        if request.method == "POST":
            pic, err, file = draw_pic(request)
            return JsonResponse({"image": pic, "err": err, "file": file})


def data_detail(request):
    '''
    Analyze uploaded new dataset and return the shape of new dataset.
    '''
    if request.method == "GET":
        data = request.GET
        model_id = int(data["model_id"])
        try:
            job = Job.objects.get(id=model_id)
        except Job.DoesNotExist:
            return JsonResponse({"num": 0})
        _x = np.load(job.x_file.file)
        return JsonResponse({"num": _x.shape[1]})

    if request.method == "POST":
        file = request.FILES.get("x_test")
        num = np.load(file).shape[1]
        return JsonResponse({"num": num})


def get_result(username):
    '''
    Create the result list on the result page.
    '''
    download_to_web()
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
    '''
    Provide predict file.
    '''
    file_name = request.GET["file"] + ".txt"
    file_path = MEDIA_ROOT + 'predict/' + file_name
    def yield_file(file_n):
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
