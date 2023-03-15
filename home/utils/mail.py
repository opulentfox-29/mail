import base64
import os

import selenium
from seleniumwire import webdriver
from seleniumwire.utils import decode
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
import json
import time


username = ''
duck_name = ''
auth_duck = False


def start():
    global driver
    global wait
    options = webdriver.ChromeOptions()

    options.add_extension("home/utils/DuckDuckGo Privacy Essentials.crx")
    options.add_argument('--headless=new')
    options.add_argument('--disable-gpu')

    try:
        driver = webdriver.Chrome(
            options=options
        )
    except selenium.common.exceptions.SessionNotCreatedException as exc:
        if "This version of ChromeDriver only supports Chrome version" in str(exc):
            your_version = str(exc).split("supports Chrome version ")[1].split('\n')[0]
            need_version = str(exc).split("browser version is ")[1].split(' ')[0]
            print("you need update ChromeDriver")
            print(f"your chromedriver version is {your_version}")
            print(f"you need download {need_version}")
            print("https://chromedriver.chromium.org/downloads")
            exit()
        else:
            raise exc

    wait = WebDriverWait(driver, 60)
    wait.until(ec.new_window_is_opened(driver.window_handles))
    driver.switch_to.window(driver.window_handles[1])
    driver.close()
    driver.switch_to.window(driver.window_handles[0])


def login(login, password, duck):
    global duck_name
    global username
    username = login
    duck_name = duck
    driver.get('https://account.proton.me/login')

    wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'input[id="username"]')))

    driver.find_element(By.CSS_SELECTOR, 'input[id="username"]').send_keys(username)
    driver.find_element(By.CSS_SELECTOR, 'input[id="password"]').send_keys(password)
    driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()

    driver.wait_for_request('https://mail.proton.me/login', 60)
    driver.get('https://mail.proton.me/u/0/all-mail')
    return {'status': True}


def get_messages(page=1):
    request = driver.wait_for_request('https://mail.proton.me/api/mail/v4/messages\?Page=.&PageSize=50&Limit=100&LabelID=5&Sort=Time&Desc=1', 60)
    body = decode(request.response.body, request.response.headers.get('Content-Encoding', 'identity'))
    messages_json = json.loads(body)
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
        if sender_address == username:
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
        del driver.requests
        driver.get(f'https://mail.proton.me/u/0/all-mail#page={page}')
        messages.extend(get_messages(page))

    return messages


def main_page():
    del driver.requests
    driver.get('https://mail.proton.me/u/0/all-mail')


def default_folder(folder_name, sender='', service_messages=(), service_folder=False,
                   invisible_folder=False, unread=False, int_time=0, str_time='', messages=()):
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


def sort_messages(messages: list[dict, ...]) -> list[dict, ...]:
    """Сортирует письма по папкам."""
    undefined_folder = default_folder(folder_name='undefined', service_folder=True, sender=username)
    folders = [undefined_folder,
               default_folder(folder_name='DuckDuckGo', service_folder=True,
                              invisible_folder=True, sender='support@duck.com')]

    for mess in reversed(messages):
        undefined = True
        if mess['sender_address'] == username and '_initialization_' in mess['subject']:
            # инициализация папки
            folders.append(default_folder(folder_name=mess['subject'].split('_initialization_')[0],
                                          sender=mess['recipients'][0]['address'],
                                          service_messages=[mess],
                                          unread=mess['unread'],
                                          int_time=mess['time'],
                                          str_time=time.strftime("%H:%M:%S %d.%m.%Y", time.localtime(mess['time'])),
                                          ))
            continue
        if mess['sender_address'] == username and '_RENAME_FOLDER_' in mess['subject']:
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


def send_message(to, subject=None, letter=None):
    driver.find_element(By.CSS_SELECTOR, 'button[data-testid="sidebar:compose"]').click()
    wait.until(ec.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-testid="composer:send-button"]')))

    to_composer = driver.find_element(By.CSS_SELECTOR, 'input[id^="to-composer-"]')
    subject_composer = driver.find_element(By.CSS_SELECTOR, 'input[id^="subject-composer-"]')

    to_composer.send_keys(to)
    subject_composer.send_keys(subject)

    iframe = driver.find_element(By.CSS_SELECTOR, 'iframe[data-testid="rooster-iframe"]')
    driver.switch_to.frame(iframe)

    editor = driver.find_element(By.CSS_SELECTOR, 'div[id="rooster-editor"]')
    editor.clear()

    editor.send_keys(letter)

    driver.switch_to.default_content()

    driver.find_element(By.CSS_SELECTOR, 'button[data-testid="composer:send-button"]').click()


def send_message_from_folder(folder: dict, send_to: str, subject=None, letter=None) -> None:
    """Отправляет письма, находясь в папке."""
    if folder['sender'] not in send_to and folder['sender'] != username:
        send_to = send_to.replace('@', '_at_') + '_' + folder['sender']
    send_message(send_to, subject, letter)


def read_message(message_id: str, full=False) -> webdriver or dict[str, str]:
    """Читает сообщение по айди."""
    # del driver.requests
    url = f'https://mail.proton.me/u/0/all-mail/{message_id}'

    driver.get(url)
    wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'iframe[data-testid="content-iframe"]')))

    iframe = driver.find_element(By.CSS_SELECTOR, 'iframe[data-testid="content-iframe"]')
    driver.switch_to.frame(iframe)
    wait.until(ec.invisibility_of_element_located((By.CSS_SELECTOR, 'span[class^="proton-image-placeholder"]')))
    wait.until_not(ec.visibility_of_element_located((By.CSS_SELECTOR, 'span[class^="proton-sr-only"]')))

    html = driver.find_element(By.CSS_SELECTOR, 'html')
    if full:
        styles = html.find_elements(By.TAG_NAME, 'style')
        for style in styles:
            if style.get_attribute('innerHTML').startswith('article,aside,datalist,details,dialog,'):
                style = style.get_attribute("outerHTML")
                break
        else:
            style = ''
        try:
            svg = html.find_element(By.CSS_SELECTOR, 'svg[class="proton-hidden"]').get_attribute("outerHTML")
        except Exception:
            svg = ''
        imgs = html.find_elements(By.TAG_NAME, 'img')
        backs = html.find_elements(By.XPATH, '//*[@background]')

        html = html.get_attribute('outerHTML').replace(style, '').replace(svg, '')

        img_urls = [img.get_attribute("src") for img in imgs]
        img_urls += [back.get_attribute("background") for back in backs]

        driver.execute_script("window.open('');")
        driver.switch_to.window(driver.window_handles[1])

        if img_urls:
            driver.get(img_urls[0])
        for img_url in img_urls:

            result = driver.execute_async_script("""
                var uri = arguments[0];
                var callback = arguments[1];
                var toBase64 = function(buffer){for(var r,n=new Uint8Array(buffer),t=n.length,a=new Uint8Array(4*Math.ceil(t/3)),i=new Uint8Array(64),o=0,c=0;64>c;++c)i[c]="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/".charCodeAt(c);for(c=0;t-t%3>c;c+=3,o+=4)r=n[c]<<16|n[c+1]<<8|n[c+2],a[o]=i[r>>18],a[o+1]=i[r>>12&63],a[o+2]=i[r>>6&63],a[o+3]=i[63&r];return t%3===1?(r=n[t-1],a[o]=i[r>>2],a[o+1]=i[r<<4&63],a[o+2]=61,a[o+3]=61):t%3===2&&(r=(n[t-2]<<8)+n[t-1],a[o]=i[r>>10],a[o+1]=i[r>>4&63],a[o+2]=i[r<<2&63],a[o+3]=61),new TextDecoder("ascii").decode(a)};
                var xhr = new XMLHttpRequest();
                xhr.responseType = 'arraybuffer';
                xhr.onload = function(){ callback(toBase64(xhr.response)) };
                xhr.onerror = function(){ callback(xhr.status) };
                xhr.open('GET', uri);
                xhr.send();
                """, img_url)
            img_url = img_url.replace('&', '&amp;')
            html = html.replace(img_url, "data:image/png;base64," + result)

        driver.close()
        driver.switch_to.window(driver.window_handles[0])

        return {'html': html}
    return html


def login_duckduckmail():
    """Авторизация в duckduckmail, происходит один раз в сеансе приложения при попытке создать папку."""
    main_page()
    driver.execute_script("window.open('https://duckduckgo.com/email/login');")
    driver.switch_to.window(driver.window_handles[1])

    wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'input[name="user"]'))).send_keys(duck_name)
    wait.until(ec.element_to_be_clickable((By.CSS_SELECTOR, 'button'))).click()
    driver.switch_to.window(driver.window_handles[0])
    while True:
        try:
            request = driver.wait_for_request('https://mail.proton.me/api/core/v4/events/.{1,100}=='
                                              '\?ConversationCounts=1&MessageCounts=1', 60)
            body = decode(request.response.body, request.response.headers.get('Content-Encoding', 'identity'))
            update = json.loads(body)

            message_id = update['Messages'][0]['ID']
            break
        except Exception:
            pass

    html = read_message(message_id)
    url = html.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
    driver.get('https://mail.proton.me/u/0/all-mail/')
    driver.switch_to.window(driver.window_handles[1])
    driver.get(url)
    wait.until(ec.element_to_be_clickable((By.CSS_SELECTOR, 'button[class="NewButton '
                                                            'AutofillSettingsPanel__GeneratorButton"]')))
    driver.close()
    driver.switch_to.window(driver.window_handles[0])


def get_new_email_address():
    driver.execute_script("window.open('https://duckduckgo.com/email/settings/autofill');")
    driver.switch_to.window(driver.window_handles[1])
    wait.until(ec.element_to_be_clickable((By.CSS_SELECTOR, 'button[class="NewButton '
                                                            'AutofillSettingsPanel__GeneratorButton"]')))

    driver.find_element(By.CSS_SELECTOR, 'button[class="NewButton '
                                         'AutofillSettingsPanel__GeneratorButton"]').click()
    wait.until(ec.element_to_be_clickable((By.CSS_SELECTOR, 'button[class="NewButton '
                                                            'AutofillSettingsPanel__GeneratorButton"]')))
    new_email = driver.find_element(By.CSS_SELECTOR, 'div[class="AutofillSettingsPanel__'
                                                     'PrivateDuckAddress "]').text.split('\n')[0]
    driver.close()
    driver.switch_to.window(driver.window_handles[0])

    return new_email


def delete_message(message_id):
    url = f'https://mail.proton.me/u/0/all-mail/{message_id}'
    driver.get(url)
    wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'button[data-testid="message-header-'
                                                                  'expanded:move-to-trash"]')))
    driver.find_element(By.CSS_SELECTOR, 'button[data-testid="message-header-expanded:move-to-trash"]').click()
    wait.until(ec.visibility_of_element_located((By.XPATH, '//span[contains( text(), '
                                                           '"Сообщение перемещено в Корзина.")]')))

    # driver.get(url)
    wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'button[data-testid="message-'
                                                                  'header-expanded:more-dropdown"]')))
    driver.find_element(By.CSS_SELECTOR, 'button[data-testid="message-header-expanded:more-dropdown"]').click()
    wait.until(ec.visibility_of_element_located((By.XPATH, '//span[contains( text(), "Удалить")]')))
    driver.find_element(By.XPATH, '//span[contains( text(), "Удалить")]').click()

    wait.until(ec.visibility_of_element_located((By.XPATH, '//button[contains( text(), "Удалить")]')))
    driver.find_element(By.XPATH, '//button[contains( text(), "Удалить")]').click()


def init_new_folder(name, description=None):
    global auth_duck
    if not auth_duck:
        login_duckduckmail()
        auth_duck = True
    new_email = get_new_email_address()
    subject = f"{name}_initialization_{new_email}"
    send_message(new_email, subject, description)


def rename_folder(new_name, folder, description=None):
    subject = f"{new_name}_RENAME_FOLDER_{folder['folder_name']}"
    send_message(folder['sender'], subject, description)


def deactivate_mail(folder):
    message_id = folder['messages'][0]['id']
    url = read_message(message_id).find_element(By.TAG_NAME, 'a').get_attribute('href')

    driver.execute_script(f"window.open('{url}');")
    driver.switch_to.window(driver.window_handles[-1])
    wait.until(ec.visibility_of_element_located((By.XPATH, '//a[contains( text(), "Deactivate")]')))
    driver.find_element(By.XPATH, '//a[contains( text(), "Deactivate")]').click()
    wait.until(ec.visibility_of_element_located((By.XPATH, '//a[contains( text(), "Reactivate This Address")]')))
    driver.close()
    driver.switch_to.window(driver.window_handles[0])
    driver.get('https://mail.proton.me/u/0/all-mail/')


def delete_folder(folder):
    deactivate_mail(folder)
    for mess in folder['messages']:
        delete_message(mess['id'])
    for mess in folder['service_messages']:
        delete_message(mess['id'])
