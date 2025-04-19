from django.urls import path
from . import views

urlpatterns = [
    path('', views.handle_uploaded_files, name='upload_files'),
]
