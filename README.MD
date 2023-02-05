Почтовый клиент, позволяющий создавать папки(с отдельным почтовым адресом) для каждого отдельного аккаунта.

# Установка
```
pip install -r requirements.txt
```
```
python manage.py migrate
```

# Преднастройка
 - Зарегестрируйтесь в почте https://mail.proton.me/
 - В настройках протона "вид почтового ящика" должен быть "ряд".
 - В настройках "Сообщения и написание" в пунке "Сообщения" ( https://account.proton.me/u/1/mail/general#messages ) включите функцию "Автоматический показ встроенных изображений" и выключите функцию "Группировка сообщений в цепочки".
 - Зарегестрируйте `DuckDuckGo email protection` ( https://duckduckgo.com/email/ ) на свой почтовый ящик протона.

# запуск
```
python manage.py runserver
```
 - Перейдите по адресу http://127.0.0.1:8000/login/
 - Введите свой логин, пароль от Proton mail, а так же никнейм от DuckDuckGo.
 - После авторизации нажмите кнопку `refsresh`

# 
![Login](https://github.com/opulentfox-29/mail/raw/master/docs/1.png)
![Folders](https://github.com/opulentfox-29/mail/raw/master/docs/2.png)
![Messages](https://github.com/opulentfox-29/mail/raw/master/docs/3.png)
![Mesage](https://github.com/opulentfox-29/mail/raw/master/docs/4.png)
