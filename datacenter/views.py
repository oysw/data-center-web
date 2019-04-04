# coding:utf-8
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
# Create your views here.
from datacenter.calc import core

@login_required
def index(request):
    return render(request, 'datacenter/index.html')

@login_required
def calc(request):
    if request.method == 'POST':
        x = request.FILES.get('x_file', None)
        y = request.FILES.get('y_file', None)

        result = core.file_read(x, y)
        print(result)
        return render(request, 'datacenter/result.html', result)

