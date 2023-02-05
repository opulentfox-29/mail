import json

from channels.consumer import SyncConsumer

from home.models import Proton
from .utils import mail
mail.start()


class WebConsumer(SyncConsumer):
    def websocket_connect(self, event):
        print('connect')
        self.send({"type": "websocket.accept"})

    def websocket_receive(self, event):
        print('receive')
        data = json.loads(event['text'])

        if data['url'] == 'login':
            login = data['login']
            password = data['password']
            duck_name = data['duck_name']
            self._block()
            status = mail.login(login, password, duck_name)
            self._unblock()
            if status:
                proton = Proton.objects.first()
                proton.login = login
                proton.password = password
                proton.duck_name = duck_name
                proton.save()

                context = {
                    'url': 'login',
                    'status': 'redirect',
                }
                self._send_ws(context)

            else:
                context = {
                    'url': 'login',
                    'status': status['err'],
                }
                self._send_ws(context)

        if data['url'] == 'folders':
            if data['status'] == 'refresh':
                self._block()
                mail.main_page()
                folders = mail.sort_messages(mail.get_messages())

                context = {
                    'url': 'folders',
                    'data': folders,
                }
                self._send_ws(context)
                self._unblock()

            if data['status'] == 'create folder':
                folder_name = data['folder_name']
                description = data['description']
                self._block()
                mail.init_new_folder(folder_name, description)
                self._unblock()

            if data['status'] == 'rename folder':
                folder_name = data['folder_name']
                description = data['description']
                folder = data['folder']
                self._block()
                mail.rename_folder(folder_name, folder, description)
                self._unblock()

            if data['status'] == 'delete folder':
                folder = data['folder']
                self._block()
                mail.delete_folder(folder)
                self._unblock()

            if data['status'] == 'send message':
                folder = data['folder']
                address = data['address']
                subject = data['subject']
                message = data['message']

                self._block()
                mail.send_message_from_folder(folder, address, subject, message)
                self._unblock()

        if data['url'] == 'messages':
            if data['status'] == 'read_message':
                self._block()
                read_message = mail.read_message(data['id'], True)['html']
                context = {
                    'url': 'messages',
                    'status': 'read_message',
                    'message': read_message,
                }
                self._send_ws(context)
                self._unblock()

        if data['url'] == 'read message':
            if data['status'] == 'delete message':
                message_id = data['id']
                self._block()
                mail.delete_message(message_id)
                self._unblock()

    def websocket_disconnect(self, event):
        print('disconnect')

    def _send_ws(self, context):
        data_json = json.dumps(context)
        self.send({
            "type": "websocket.send",
            "text": str(data_json),
        })

    def _block(self):
        context = {'url': '*', 'status': 'block'}
        self._send_ws(context)

    def _unblock(self):
        context = {'url': '*', 'status': 'unblock'}
        self._send_ws(context)
