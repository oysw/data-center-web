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
        return render(request, 'upload.html')
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
            return render(request, 'upload.html')
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
def upload(request):
    """
    Get and save the uploaded file and process the file with function provide by pymatgen and matminer.
    The information of uploaded file will be stored in database.
    :param request:
    :return:
    """
    if request.method == "POST":
        file = request.FILES.get('file')
        if file is None:
            return render(request, 'upload.html', {'error': 'Please choose a file!'})
        status, df = preprocess([], file)
    else:
        featurizer = request.GET["featurizer"]
        target = request.GET["targetColumn"]
        try:
            value = request.GET["value"]
        except KeyError:
            value = ""
        option = [featurizer, target, value]
        job_id = request.session["job_id"]
        status, df = preprocess(option, Job.objects.get(id=job_id).data)
    """
    If the process of data succeeds without error reports, save new data in database.
    """
    if status:
        f = File(BytesIO())
        df.to_pickle(f, compression=None)
        try:
            # Data which has been uploaded and experience several processes will come to this way.
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
            # Data that is first uploaded will come to this way.(Raw uploaded data.)
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


@login_required
def submit(request):
    """
    Submit the job and begin calculating
    :param request:
    :return:
    """
    columns = list(request.POST)[1:]
    job_id = request.session["job_id"]
    file_path = request.session["job_file_path"]
    job = Job.objects.get(id=job_id)
    df = pd.read_pickle(job.data, compression=None)
    df = df[columns]
    job.data.close()
    try:
        os.remove(MEDIA_ROOT + file_path)
    except FileNotFoundError:
        pass
    f = File(BytesIO())
    df.to_pickle(f, compression=None)
    f.name = file_path.split("/")[-1]
    job.data = f
    job.status = "W"
    job.save()
    try:
        del request.session["job_id"]
        del request.session["job_file_path"]
    except KeyError:
        pass
    return render(request, "upload.html")


@login_required
def logout(request):
    """
    :param request:
    :return:
    """
    auth.logout(request)
    return redirect('/')


@login_required
def result(request):
    """
    Jump to result page.
    :param request:
    :return:
    """
    if 'username' in request.session.keys():
        return render(request, 'result.html', {'result': get_result(request.session['username'])})
    else:
        return render(request, "index.html")


@login_required
def draw(request):
    """
    Return graph html code generated by plotly and predict data.
    Predict data will be save in directory /tmp/ai4chem/predict/.
    The file name will be username.txt.
    :param request:
    :return:
    Ajax:
    image: Scalable graph's HTML code. (If error occurs, this will be empty.)
    err: Text explaining which error occurs.
    GET:
    Jump to graph making page.
    """
    if request.is_ajax():
        if request.method == "POST":
            pic, err = draw_pic(request)
            return JsonResponse({"image": pic, "err": err})
    else:
        job_id = request.GET["jobId"]
        return render(request, "draw.html", {"jobId": job_id})


@login_required
def get_data_columns(request):
    """
    Return the columns of dataframe(Pandas) for generation of choices of target columns.
    :param request:
    :return:
    """
    model_id = int(request.GET["model_id"])
    job = Job.objects.get(id=model_id)
    df = pd.read_pickle(job.data, compression=None)
    job.data.close()
    return JsonResponse({"label": list(df.columns)})


@login_required
def data_preprocess(request):
    """
    This function is used to process temporary uploaded file. (i.e. Upload new data for prediction).
    File will be save with username in MEDIA_ROOT directory. The information of data will not be stored in database.
    GET:
    The request must contain these parameter:
    featurizer: Method provided by matminer or pymatgen to featurize dataframe(Pandas)
    target_column: Which column need featurizing.
    value(optional): Extra information needed by featurizer. (e.g. User need to provide new name for rename method)
    POST:
    This function also used to receive uploaded data.
    :param request:
    :return:
    label: The column of dataframe(Pandas)
    html: Table of data(HTML format)
    err: Possible error while saving the file.
    """
    file_name = MEDIA_ROOT + request.session["username"]
    if request.method == "GET":
        featurizer = request.GET["featurizer"]
        target = request.GET["targetColumn"]
        try:
            value = request.GET["value"]
        except KeyError:
            value = ""
        option = [featurizer, target, value]
        file = open(file_name, "rb")
        status, df = preprocess(option, file)
    else:
        file = request.FILES.get("uploadFile")
        status, df = preprocess([], file)
    if status:
        data = df
        df.to_pickle(file_name, compression=None)
    else:
        return JsonResponse({"err": df})
    return_dict = {
        "label": list(data.columns),
        "html": mark_safe(data.to_html())
    }
    return JsonResponse(return_dict)


def get_result(username):
    """
    Create the result list for the result page.
    :param username:
    :return: Query list of job's records.
    """
    jobs = Job.objects.filter(owner=username, status='F')
    for job in jobs:
        try:
            mod = job.mod.file
            mod = joblib.load(mod)
            job.mod = mod.__class__.__name__
        except FileNotFoundError:
            job.mod = ''
    return jobs


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
