from django.shortcuts import render
from django.views.generic.base import TemplateView
from django.views.generic import DetailView

from home.models import Proton


class Login(DetailView):
    model = Proton
    template_name = 'home/login.html'

    def get_object(self, queryset=None):
        data = Proton.objects.first()
        if not data:
            data = Proton.objects.create(login='', password='', duck_name='')
        return data

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        data = context['object']

        data = {
            'login': data.login,
            'password': data.password,
            'duck_name': data.duck_name,
        }
        context.update(data)
        return context


class Folders(TemplateView):
    template_name = 'home/folders.html'
