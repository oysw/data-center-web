"""
Request handler.
"""
from io import BytesIO
import pandas as pd
import joblib
from django.shortcuts import render, redirect
from django.contrib import auth
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.http import StreamingHttpResponse
from django.utils.safestring import mark_safe
from django.core.files import File
from django.core.cache import cache
from django.views.decorators.cache import cache_page
from django.contrib.auth.decorators import login_required
from ai4chem.tools import username_check
from django.utils.crypto import get_random_string
from ai4chem.models import Job
from ai4chem.tools import draw_pic, preprocess
from datacenter.settings import MEDIA_ROOT
from ai4chem.tasks import featurize, calculate
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
    if request.user.username != "":
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
            auth.logout(request)
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


@cache_page(20)
@login_required
def home(request):
    """
    Jump to home page.
    :param request:
    :return:
    """
    username = request.user.username
    jobs = Job.objects.filter(owner=username)
    for job in jobs:
        try:
            best = joblib.load(job.mod)
            job.mod = best.__class__.__name__
        except ValueError:
            pass
        except FileNotFoundError:
            job.mod = "Not available"
    return_dict = {'username': username, 'jobs': jobs}
    return render(request, 'home.html', return_dict)


@login_required
@cache_page(5 * 60)
def home_error(request):
    """
    :param request:
    :return:
    """
    job_id = request.GET["job_id"]
    error = cache.get(job_id + "_error")
    return JsonResponse({"report": repr(error)})


@login_required
def add_new_job(request):
    """
    :param request:
    :return:
    """
    username = request.user.username
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
        # Avoid repeatedly requests submission.
        pass
    return home(request)


@login_required
def upload_page(request):
    """
    :param request:
    :return:
    """
    file_info = {
        'job_id': request.GET['job_id'],
        'choose_data': request.GET['choose_data']
    }
    return render(request, 'upload.html', file_info)


@login_required
def upload(request):
    """
    Receive uploaded data and save it in the database.
    :param request:
    :return:
    """
    file = request.FILES.get('file')
    try:
        # To avoid potential page error.
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
    # Save the file according to its type.
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
    """
    Jump to process page.
    :param request:
    :return:
    """
    job_id = int(request.GET['job_id'])
    res = cache.get("job_featurize_" + str(job_id))
    if res is None or res.ready():
        cache.set("job_featurize_" + str(job_id), None)
        choose_data = request.GET['choose_data']
        job = Job.objects.get(id=job_id)
        return_dict = {
            'job_id': job_id,
            'choose_data': choose_data,
        }
        try:
            if choose_data == 'raw':
                df = pd.read_pickle(job.raw, compression=None)
            elif choose_data == 'upload':
                df = pd.read_pickle(job.upload, compression=None)
            else:
                return render(request, 'process.html')
        except FileNotFoundError:
            return_dict["error"] = "Your data has been deleted. Please contact administrator."
            return render(request, 'process.html', return_dict)
        cache_graph = cache.get(str(job_id) + "_" + choose_data + "_html_graph")
        # Read the html-format table code from cache.
        if cache_graph is not None:
            html = cache_graph
        else:
            # Cache is expired
            html = mark_safe(df.to_html(classes=['table', 'table-striped', 'table-bordered', 'text-nowrap']))
        # Update the graph by writing new html-format table code generated by pandas into cache.
        cache.set(str(job_id) + "_" + choose_data + "_html_graph", html)
        return_dict['html'] = html
    # If the job is still under processing, send a signal to inform front page to avoid new task submission.
    else:
        return_dict = {
            'processing': True
        }
    return render(request, 'process.html', return_dict)


@login_required
def process(request):
    """
    Submit new conversion task and start a new thread for processing.
    :param request:
    :return:
    """
    featurizer = request.GET["featurizer"]
    target = request.GET["target_column"]
    try:
        value = request.GET["value"]
    except KeyError:
        value = ""
    try:
        extra = request.GET["extra"]
    except KeyError:
        extra = ""
    job_id = int(request.GET["job_id"])
    choose_data = request.GET['choose_data']
    option = (job_id, featurizer, target, value, extra, choose_data)
    result = featurize.delay(option)
    cache.set("job_featurize_" + str(job_id), result, timeout=None)
    job = Job.objects.get(id=job_id)
    job.status = 'P'
    job.save()
    # Return a signal to front page to avoid new conversion task submitting.
    return_dict = {
        'processing': True
    }
    return render(request, 'process.html', return_dict)


@login_required
def submit_page(request):
    """
    Jump to submit page where job is submitted to auto machine learning calculation.
    :param request:
    :return:
    """
    job_id = request.GET['job_id']
    job_id = int(job_id)
    job = Job.objects.get(id=job_id)
    file = job.raw
    df = pd.read_pickle(file, compression=None)
    df = df[:5]
    file.close()
    columns = list(df.columns)
    return_dict = {
        'job_id': job_id,
        'columns': columns,
        'html': mark_safe(df.to_html(classes=['table', 'table-striped', 'table-bordered', 'text-nowrap']))
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
    target = request.POST['column_as_target']
    columns = list(request.POST)[2:-1]
    job = Job.objects.get(id=job_id)
    file = job.raw
    df = pd.read_pickle(file, compression=None)
    file.close()
    # Move the target column to the last.
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
    # Status from processing to waiting.
    job.status = "W"
    job.save()
    calculate.delay(job_id)
    return home(request)


@login_required
def draw_page(request):
    """
    Jump to plotting page.
    :param request:
    :return:
    """
    job_id = int(request.GET["job_id"])
    choose_data = request.GET["choose_data"]
    job = Job.objects.get(id=job_id)
    try:
        raw_df = pd.read_pickle(job.raw, compression=None)
    except FileNotFoundError:
        return render(request, "draw.html", {"error": "Your raw data has been deleted, Please contact administrator."})
    return_dict = {
        'job_id': job_id,
        'choose_data': choose_data,
        'raw_columns': list(raw_df.columns)[:-1]
    }
    if choose_data == 'upload':
        try:
            upload_df = pd.read_pickle(job.upload, compression=None)
        except FileNotFoundError:
            return render(request, "draw.html",
                          {"error": "Your uploaded data has been deleted, Please contact administrator."})
        return_dict['upload_columns'] = list(upload_df.columns)
    return render(request, "draw.html", return_dict)


@login_required
def draw(request):
    """
    :param request:
    :return:
    """
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
    file_name = request.user.username + ".txt"
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


@login_required
def download_data(request):
    """
    :param request:
    :return:
    """
    job_id = int(request.GET["job_id"])
    choose_data = request.GET["choose_data"]
    job = Job.objects.get(id=job_id)
    if choose_data == "upload":
        file = job.upload
    elif choose_data == "raw":
        file = job.raw
    else:
        return StreamingHttpResponse()

    def yield_file(file_n):
        """
        Transported by stream.
        :param file_n:
        :return:
        """
        chunk_size = 512
        while True:
            content = file_n.read(chunk_size)
            if content:
                yield content
            else:
                break
    response = StreamingHttpResponse(yield_file(file))
    response['Content-Type'] = 'application/octet-stream'
    response['Content-Disposition'] = 'attachment;filename="{}.pkl"'.format(choose_data)
    return response
