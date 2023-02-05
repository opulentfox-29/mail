from django.urls import path
from .views import Login, Folders

urlpatterns = [
    path('login/', Login.as_view()),
    path('folders/', Folders.as_view()),
]
