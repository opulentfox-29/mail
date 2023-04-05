from seleniumwire import webdriver
from seleniumwire.utils import decode
from selenium.common.exceptions import SessionNotCreatedException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

import requests
import json
import time
import os


class Mail:
    def __init__(self):
        self.current_dir = os.path.dirname(__file__)
        self.driver = None
        self.wait = None
        self.username = ''
        self.duck_name = ''
        self.auth_duck = None
        self.auth_token = ''

        self.__start()

    def __del__(self):
        self.driver.quit()

    def login(self, username: str, password: str, duck_name: str) -> True or None:
        """Авторизация в mail.proton.me"""
        self.username = username
        self.duck_name = duck_name

        self.driver.get('https://account.proton.me/login')
        self.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'input[id="username"]')))

        self.driver.find_element(By.CSS_SELECTOR, 'input[id="username"]').send_keys(self.username)
        self.driver.find_element(By.CSS_SELECTOR, 'input[id="password"]').send_keys(password)
        self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()

        self.driver.wait_for_request('https://mail.proton.me/login', 60)
        self.driver.get('https://mail.proton.me/u/0/all-mail')
        self.driver.wait_for_request(
            r'https://mail.proton.me/api/mail/v4/messages\?Page=.&PageSize=50&Limit=100&LabelID=5&Sort=Time&Desc=1', 60)

        self.__get_auth_token()

        return True

    def get_sorted_messages(self) -> list[dict, ...]:
        """Сортирует письма по папкам."""
        messages = self.__get_messages()
        undefined_folder = self.__default_folder(folder_name='undefined', service_folder=True, sender=self.username)
        folders = [
            undefined_folder,
            self.__default_folder(folder_name='DuckDuckGo', service_folder=True,
                                  invisible_folder=True, sender='support@duck.com')
        ]

        for mess in reversed(messages):
            undefined = True
            if mess['sender_address'] == self.username and '_initialization_' in mess['subject']:
                # инициализация папки
                folders.append(
                    self.__default_folder(
                        folder_name=mess['subject'].split('_initialization_')[0],
                        sender=mess['recipients'][0]['address'],
                        service_messages=[mess],
                        unread=mess['unread'],
                        int_time=mess['time'],
                        str_time=time.strftime("%H:%M:%S %d.%m.%Y", time.localtime(mess['time'])),
                    )
                )
                continue
            if mess['sender_address'] == self.username and '_RENAME_FOLDER_' in mess['subject']:
                # переименование папки
                new_name, old_name = mess['subject'].split('_RENAME_FOLDER_')
                for folder in folders:
                    if folder['folder_name'] == old_name:
                        folder['folder_name'] = new_name
                        folder['service_messages'].append(mess)
                        break
                continue

            for folder in folders[1:]:
                # добавление писем в существующие папки
                if not mess['recipients']:
                    # скип писем без папок и черновиков
                    continue
                if folder['sender'] in mess['recipients'][0]['address'] or folder['sender'] in mess['sender_address']:
                    # добавление письма в папку
                    undefined = False
                    folder['messages'].insert(0, mess)
                    if mess['unread']:
                        folder['unread'] = mess['unread']
                    if mess['time'] > folder['int_time']:
                        folder['int_time'] = mess['time']
                        folder['str_time'] = time.strftime("%H:%M:%S %d.%m.%Y", time.localtime(mess['time']))

            if undefined:
                # добавление писем без папок в папку undefined
                undefined_folder['messages'].insert(0, mess)
                if mess['unread']:
                    undefined_folder['unread'] = mess['unread']
                if mess['time'] > folders[0]['int_time']:
                    undefined_folder['int_time'] = mess['time']
                    undefined_folder['str_time'] = time.strftime("%H:%M:%S %d.%m.%Y", time.localtime(mess['time']))

        folders.sort(key=lambda x: x['int_time'])
        return folders

    def send_message_from_folder(self, folder: dict, send_to: str, subject=None, letter=None) -> None:
        """Отправляет письма, находясь в папке."""
        if folder['sender'] not in send_to and folder['sender'] != self.username:
            send_to = send_to.replace('@', '_at_') + '_' + folder['sender']
        self.__send_message(send_to, subject, letter)

    def read_message(self, message_id: str, full=False) -> webdriver or str:
        """Читает письмо по ID."""
        url = f'https://mail.proton.me/u/0/all-mail/{message_id}'

        self.driver.get(url)
        self.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'iframe[data-testid="content-iframe"]')))

        iframe = self.driver.find_element(By.CSS_SELECTOR, 'iframe[data-testid="content-iframe"]')
        self.driver.switch_to.frame(iframe)
        self.wait.until(
            ec.invisibility_of_element_located((By.CSS_SELECTOR, 'span[class^="proton-image-placeholder"]')))
        self.wait.until_not(ec.visibility_of_element_located((By.CSS_SELECTOR, 'span[class^="proton-sr-only"]')))

        html_driver = self.driver.find_element(By.CSS_SELECTOR, 'html')
        if full:  # Чтение изображений, перевод страницы из драйвера в HTML
            formula = '{for(var r,n=new Uint8Array(buffer),t=n.length,a=new Uint8Array(4*Math.ceil(t/3)),'\
                      'i=new Uint8Array(64),o=0,c=0;64>c;++c)i[c]="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi'\
                      'jklmnopqrstuvwxyz0123456789+/".charCodeAt(c);for(c=0;t-t%3>c;c+=3,o+=4)r=n[c]'\
                      '<<16|n[c+1]<<8|n[c+2],a[o]=i[r>>18],a[o+1]=i[r>>12&63],a[o+2]=i[r>>6&63],a[o+3]'\
                      '=i[63&r];return t%3===1?(r=n[t-1],a[o]=i[r>>2],a[o+1]=i[r<<4&63],a[o+2]=61,'\
                      'a[o+3]=61):t%3===2&&(r=(n[t-2]<<8)+n[t-1],a[o]=i[r>>10],a[o+1]=i[r>>4&63],'\
                      'a[o+2]=i[r<<2&63],a[o+3]=61),new TextDecoder("ascii").decode(a)};'
            styles = html_driver.find_elements(By.TAG_NAME, 'style')
            for style in styles:
                if style.get_attribute('innerHTML').startswith('article,aside,datalist,details,dialog,'):
                    style = style.get_attribute("outerHTML")
                    break
            else:
                style = ''
            try:
                svg = html_driver.find_element(By.CSS_SELECTOR, 'svg[class="proton-hidden"]').get_attribute("outerHTML")
            except Exception:
                svg = ''
            imgs = html_driver.find_elements(By.TAG_NAME, 'img')
            backs = html_driver.find_elements(By.XPATH, '//*[@background]')

            html = html_driver.get_attribute('outerHTML').replace(style, '').replace(svg, '')

            img_urls = [img.get_attribute("src") for img in imgs]
            img_urls += [back.get_attribute("background") for back in backs]

            self.driver.execute_script("window.open('');")
            self.driver.switch_to.window(self.driver.window_handles[1])

            if img_urls:
                self.driver.get(img_urls[0])
            for img_url in img_urls:
                result = self.driver.execute_async_script(
                    "var uri = arguments[0];"
                    "var callback = arguments[1];"
                    f"var toBase64 = function(buffer){formula}"
                    "var xhr = new XMLHttpRequest();"
                    "xhr.responseType = 'arraybuffer';"
                    "xhr.onload = function(){ callback(toBase64(xhr.response)) };"
                    "xhr.onerror = function(){ callback(xhr.status) };"
                    "xhr.open('GET', uri);"
                    "xhr.send();",
                    img_url)
                img_url = img_url.replace('&', '&amp;')
                html = html.replace(img_url, "data:image/png;base64," + result)

            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])

            return html
        return html_driver

    def delete_messages(self, *messages_id: str) -> None:
        """Удалить письма."""
        headers = {
            "x-pm-appversion": "web-mail@5.0.19.5",
            "x-pm-uid": self.auth_token[0],
        }

        cookies = {
            "AUTH-" + self.auth_token[0]: self.auth_token[1],
        }

        payload = {
            "IDs": [message_id.split("#page=")[0] for message_id in messages_id],
        }

        requests.put('https://mail.proton.me/api/mail/v4/messages/delete', headers=headers, cookies=cookies,
                     json=payload)

    def init_new_folder(self, name: str, description: str = None) -> None:
        """Создание новой папки."""
        if self.auth_duck is None:
            self.__check_duckduckmail()
        if not self.auth_duck:
            self.__login_duckduckmail()
            self.auth_duck = True
        new_email = self.__get_new_email_address()
        subject = f"{name}_initialization_{new_email}"
        self.__send_message(new_email, subject, description)

    def rename_folder(self, new_name: str, folder: dict, description: str = None) -> None:
        """Переименовать папку."""
        subject = f"{new_name}_RENAME_FOLDER_{folder['folder_name']}"
        self.__send_message(folder['sender'], subject, description)

    def delete_folder(self, folder: dict) -> None:
        self.__deactivate_mail(folder)
        for mess in folder['messages']:
            self.delete_messages(mess['id'])
        for mess in folder['service_messages']:
            self.delete_messages(mess['id'])

    def __start(self) -> None:
        """Создание веб драйвера."""
        options = webdriver.ChromeOptions()

        options.add_extension(f"{self.current_dir}/DuckDuckGo Privacy Essentials.crx")
        options.add_argument(f"user-data-dir={self.current_dir}/profile")
        options.add_argument('--headless=new')  # Отключение графического интерфейса веб драйвера.
        options.add_argument('--disable-gpu')

        try:
            self.driver = webdriver.Chrome(
                options=options
            )
        except SessionNotCreatedException as exc:
            if "This version of ChromeDriver only supports Chrome version" in str(exc):
                your_version = str(exc).split("supports Chrome version ")[1].split('\n')[0]
                need_version = str(exc).split("browser version is ")[1].split(' ')[0]
                print("You need update ChromeDriver\n"
                      f"Your ChromeDriver version is {your_version}\n"
                      f"You need download ChromeDriver {need_version}\n"
                      "And put it in home/utils/\n"
                      "https://chromedriver.chromium.org/downloads")
                exit()
            else:
                raise exc

        self.wait = WebDriverWait(self.driver, 60)
        if not os.path.exists(f'{self.current_dir}/profile'):
            self.wait.until(ec.new_window_is_opened(self.driver.window_handles))
            self.driver.switch_to.window(self.driver.window_handles[1])
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])

    def __get_auth_token(self) -> None:
        """Получение токена авторизации."""
        self.driver.get('https://mail.proton.me/api/')
        cookies = self.driver.get_cookies()
        self.auth_token = next((c['name'][5:], c['value']) for c in cookies if c['name'].startswith('AUTH-'))
        self.__main_page()

    def __get_messages(self, page: int = 1) -> list:
        """Получить список всех сообщений."""
        headers = {
            "x-pm-appversion": "web-mail@5.0.19.5",
            "x-pm-uid": self.auth_token[0],
        }

        cookies = {
            "AUTH-" + self.auth_token[0]: self.auth_token[1],
        }

        payload = {
            "Page": page - 1,
            "PageSize": "50",
            "Limit": "100",
            "LabelID": "5",
            "Sort": "Time",
            "Desc": "1",
        }

        response = requests.get('https://mail.proton.me/api/mail/v4/messages',
                                headers=headers, cookies=cookies, data=payload, params=payload)
        messages_json = response.json()
        messages = []
        page_id = page
        for i, message_json in enumerate(messages_json['Messages']):
            if i == 50:
                page_id += 1
            message_id = message_json.get('ID') + f"#page={page_id}"
            conversation_id = message_json.get('ConversationID')
            subject = message_json.get('Subject')
            unread = message_json.get('Unread')
            sender_address = message_json.get('SenderAddress')
            sender_name = message_json.get('SenderName')
            time_mess = message_json.get('Time')

            recipients = []
            for recipient in message_json.get('ToList'):
                address = recipient.get('Address')
                name = recipient.get('Name', address)

                recipients.append({
                    'name': name,
                    'address': address
                })
            if not sender_name:
                sender_name = sender_address

            i_sender = False
            if sender_address == self.username:
                i_sender = True

            messages.append({
                'id': message_id,
                'conversation_id': conversation_id,
                'subject': subject,
                'unread': unread,
                'time': time_mess,
                'str_time': time.strftime("%H:%M:%S %d.%m.%Y", time.localtime(time_mess)),
                'sender_address': sender_address,
                'sender_name': sender_name,
                'i_sender': i_sender,
                'recipients': recipients
            })
        if len(messages) == 100:
            page += 2
            messages.extend(self.__get_messages(page))
        return messages

    def __main_page(self) -> None:
        """Переход на главную страницу."""
        del self.driver.requests
        self.driver.get('https://mail.proton.me/u/0/all-mail')

    def __default_folder(self, folder_name, sender='', service_messages=(), service_folder=False,
                         invisible_folder=False, unread=False, int_time=0, str_time='', messages=()) -> dict:
        service_messages = service_messages or []
        messages = messages or []
        return {
            'folder_name': folder_name,
            'sender': sender,
            'service_messages': service_messages,
            'service_folder': service_folder,
            'invisible_folder': invisible_folder,
            'unread': unread,
            'int_time': int_time,
            'str_time': str_time,
            'messages': messages
        }

    def __send_message(self, to: str, subject: str = None, letter: str = None) -> None:
        """Отправка письма."""
        self.driver.find_element(By.CSS_SELECTOR, 'button[data-testid="sidebar:compose"]').click()
        self.wait.until(ec.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-testid="composer:send-button"]')))

        to_composer = self.driver.find_element(By.CSS_SELECTOR, 'input[id^="to-composer-"]')
        subject_composer = self.driver.find_element(By.CSS_SELECTOR, 'input[id^="subject-composer-"]')

        to_composer.send_keys(to)
        subject_composer.send_keys(subject)

        iframe = self.driver.find_element(By.CSS_SELECTOR, 'iframe[data-testid="rooster-iframe"]')
        self.driver.switch_to.frame(iframe)

        editor = self.driver.find_element(By.CSS_SELECTOR, 'div[id="rooster-editor"]')
        editor.clear()
        editor.send_keys(letter)

        self.driver.switch_to.default_content()

        self.driver.find_element(By.CSS_SELECTOR, 'button[data-testid="composer:send-button"]').click()
        if not subject:
            self.driver.find_element(By.CSS_SELECTOR, 'button[data-testid="modal-footer:set-button"]').click()

    def __check_duckduckmail(self) -> None:
        """Проверка авторизации в DuckDuckMail."""
        self.driver.execute_script("window.open('https://duckduckgo.com/email/settings/autofill');")
        self.driver.switch_to.window(self.driver.window_handles[1])
        card = self.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'div[class="welcomeCardContent"]')))
        if card.text != "Enter your Duck Address":
            self.auth_duck = True
        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[0])

    def __login_duckduckmail(self) -> None:
        """Авторизация в DuckDuckMail, происходит один раз в сеансе приложения при попытке создать папку."""
        self.__main_page()
        self.driver.execute_script("window.open('https://duckduckgo.com/email/login');")
        self.driver.switch_to.window(self.driver.window_handles[1])

        self.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'input[name="user"]'))).send_keys(
            self.duck_name)
        self.wait.until(ec.element_to_be_clickable((By.CSS_SELECTOR, 'button'))).click()
        self.driver.switch_to.window(self.driver.window_handles[0])
        while True:
            try:
                request = self.driver.wait_for_request('https://mail.proton.me/api/core/v4/events/.{1,100}=='
                                                       r'\?ConversationCounts=1&MessageCounts=1', 60)
                body = decode(request.response.body, request.response.headers.get('Content-Encoding', 'identity'))
                update = json.loads(body)

                message_id = update['Messages'][0]['ID']
                break
            except Exception:
                pass

        html_driver = self.read_message(message_id)
        url = html_driver.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
        self.driver.get('https://mail.proton.me/u/0/all-mail/')
        self.driver.switch_to.window(self.driver.window_handles[1])
        self.driver.get(url)
        self.wait.until(ec.element_to_be_clickable((By.CSS_SELECTOR, 'button[class="NewButton '
                                                                     'AutofillSettingsPanel__GeneratorButton"]')))
        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[0])

    def __get_new_email_address(self) -> str:
        """Получение нового адреса почты."""
        self.driver.execute_script("window.open('https://duckduckgo.com/email/settings/autofill');")
        self.driver.switch_to.window(self.driver.window_handles[1])
        self.wait.until(ec.element_to_be_clickable((By.CSS_SELECTOR, 'button[class="NewButton '
                                                                     'AutofillSettingsPanel__GeneratorButton"]')))

        self.driver.find_element(By.CSS_SELECTOR, 'button[class="NewButton '
                                                  'AutofillSettingsPanel__GeneratorButton"]').click()
        self.wait.until(ec.element_to_be_clickable((By.CSS_SELECTOR, 'button[class="NewButton '
                                                                     'AutofillSettingsPanel__GeneratorButton"]')))
        new_email = self.driver.find_element(By.CSS_SELECTOR, 'div[class="AutofillSettingsPanel__'
                                                              'PrivateDuckAddress "]').text.split('\n')[0]
        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[0])

        return new_email

    def __deactivate_mail(self, folder: dict) -> None:
        """Деактивировать адрес почты."""
        message_id = folder['messages'][0]['id']
        url = self.read_message(message_id).find_element(By.TAG_NAME, 'a').get_attribute('href')

        self.driver.execute_script(f"window.open('{url}');")
        self.driver.switch_to.window(self.driver.window_handles[-1])
        self.wait.until(ec.visibility_of_element_located((By.XPATH, '//a[contains( text(), "Deactivate")]')))
        self.driver.find_element(By.XPATH, '//a[contains( text(), "Deactivate")]').click()
        self.wait.until(
            ec.visibility_of_element_located((By.XPATH, '//a[contains( text(), "Reactivate This Address")]')))
        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[0])
        self.driver.get('https://mail.proton.me/u/0/all-mail/')
