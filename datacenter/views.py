# coding:utf-8

from django.http import HttpResponse
from django.shortcuts import render
# Create your views here.
from .calc import core

def index(request):
    return render(request, 'index.html')

def calc(request):
    if request.method == 'POST':
        x = request.FILES.get('x_file', None)
        y = request.FILES.get('y_file', None)

        result = core.file_read(x, y)
        print(result)
        return render(request, 'result.html', result)