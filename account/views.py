from django.contrib import auth
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.shortcuts import render
import re

# Create your views here.


def index(request):
    return render(request, 'account/index.html')


def login(request):
    if 'username' in request.session.keys():
        return HttpResponseRedirect('/account/')
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user:
            auth.login(request, user)
            request.session['username'] = username
            return HttpResponseRedirect('/')
        else:
            return render(request, 'account/login.html', {'fail': '密码错误！'})
    else:
        return render(request, 'account/login.html', {})


def register(request):
    if 'username' in request.session.keys():
        return HttpResponseRedirect('')
    if request.method == 'POST':
        username = request.POST['username']
        mail = r'^[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+){0,4}@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+){0,4}$'
        if not re.match(mail, username):
            return render(request, 'account/register.html', context={'fail2' : '用户名必须是一个邮箱'})
        password = request.POST['password']
        user_list = User.objects.all()
        for each_user in user_list:
            if each_user.username == username:
                return render(request, 'account/register.html', context={'fail1': '用户名已被占用'})
        user = User.objects.create_user(username=username, password=password)
        user.save()
        auth.login(request, user)
        request.session['username'] = username
        return HttpResponseRedirect('/')
    else:
        return render(request, 'account/register.html', {})


def logout(request):
    del request.session['username']
    return HttpResponseRedirect('')
