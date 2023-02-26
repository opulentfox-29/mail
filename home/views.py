from django.shortcuts import redirect
from django.views.generic.base import TemplateView
from django.views.generic import DetailView
from rest_framework.response import Response
from rest_framework.views import APIView

from home.models import Proton
from home.serializers import ProtonSerializer
from .utils import mail

mail.start()


def home(request):
    if mail.username:
        return redirect('folders')
    return redirect('login')


class Login(DetailView):
    model = Proton
    template_name = 'home/login.html'

    def get_object(self, queryset=None):
        data = Proton.objects.first()
        if not data:
            serializer = ProtonSerializer(data={'login': '', 'password': '', 'duck_name': ''})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            data = Proton.objects.first()
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


class MailAPIView(APIView):
    def get(self, request):
        mail.main_page()
        folders = mail.sort_messages(mail.get_messages())

        context = {
            'url': 'folders',
            'data': folders,
        }
        return Response(context)

    def post(self, request):
        data = request.data

        urls = {
            'login': self._login,
            'folders': self._folders,
            'messages': self._messages,
            'read message': self._read_message,
        }

        return urls[data['url']](data)

    def _login(self, data):
        login = data['login']
        password = data['password']
        duck_name = data['duck_name']
        status = mail.login(login, password, duck_name)
        if status:
            return self._redirect(data)
        else:
            return self._error_login(status)

    def _redirect(self, data):
        instance = Proton.objects.first()
        serializer = ProtonSerializer(data=data, instance=instance)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        context = {
            'url': 'login',
            'status': 'redirect',
        }
        return Response(context)

    def _error_login(self, status):
        context = {
            'url': 'login',
            'status': 'err',
            'err': status.get('err', "Unknown error"),
        }
        return Response(context)

    def _folders(self, data):
        status = {
            'create folder': self._create_folder,
            'rename folder': self._rename_folder,
            'delete folder': self._delete_folder,
            'send message': self._send_message,
        }

        return status[data['status']](data)

    def _create_folder(self, data):
        folder_name = data['folder_name']
        description = data['description']
        mail.init_new_folder(folder_name, description)
        return Response({'status': 'continue'})

    def _rename_folder(self, data):
        folder_name = data['folder_name']
        description = data['description']
        folder = data['folder']
        mail.rename_folder(folder_name, folder, description)
        return Response({'status': 'continue'})

    def _delete_folder(self, data):
        folder = data['folder']
        mail.delete_folder(folder)
        return Response({'status': 'continue'})

    def _send_message(self, data):
        folder = data['folder']
        address = data['address']
        subject = data['subject']
        message = data['message']

        mail.send_message_from_folder(folder, address, subject, message)
        return Response({'status': 'continue'})

    def _messages(self, data):
        if data['status'] == 'read_message':
            read_message = mail.read_message(data['id'], True)['html']
            context = {
                'url': 'messages',
                'status': 'read_message',
                'message': read_message,
            }
            return Response(context)

    def _read_message(self, data):
        if data['status'] == 'delete message':
            message_id = data['id']
            mail.delete_message(message_id)
            return Response({'status': 'continue'})
