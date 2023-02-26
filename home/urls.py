from django.urls import path
from .views import Login, Folders, home

urlpatterns = [
    path('', home, name='home'),
    path('login/', Login.as_view(), name='login'),
    path('folders/', Folders.as_view(), name='folders'),
]
