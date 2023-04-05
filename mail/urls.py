from django.urls import path
from .views import MailAPIView, Login, Folders, home


urlpatterns = [
    path('', home, name='home'),
    path('api/', MailAPIView.as_view()),
    path('login/', Login.as_view(), name='login'),
    path('folders/', Folders.as_view(), name='folders'),
]
