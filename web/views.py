from django.shortcuts import render
from django.contrib import auth
from django.contrib.auth import authenticate
from django.contrib.auth.models import User

# Create your views here.

def index(request):
    print(request.session)
    return render(request, 'index.html')

def login(request):
    if 'username' in request.session.keys():
        return render(request, 'upload.html')
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        try:
            User.objects.get(username=username)
        except Exception:
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
    return render(request, 'register.html')

def upload(request):
    return render(request, 'upload.html')
