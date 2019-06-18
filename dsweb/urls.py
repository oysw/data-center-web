"""dsweb URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from core import views

urlpatterns = [
    path('', views.index),
    path('admin/', admin.site.urls),
    # Login page jumping or login info submission
    path('login/', views.login),
    # Register Page jumping or register info submission
    path('register/', views.register),
    # Home page jumping
    path('home/', views.home),
    # Add new job
    path('job/add/', views.add_new_job),
    # Delete new job
    path('job/delete/', views.delete_job),
    # Plot graph
    path('draw/', views.draw),
    # Draw page jumping
    path('draw/page/', views.draw_page),
    # Uploaded file process and save
    path('upload/', views.upload),
    # Upload page jumping
    path('upload/page/', views.upload_page),
    # Process file and save
    path('job/process/', views.process),
    # Process page jumping
    path('job/process/page/', views.process_page),
    # Confirm data page
    path('submit/page/', views.submit_page),
    path('logout/', views.logout),
    # Ajax
    path('submit/', views.submit),
    path('download/', views.download_predict),

]
