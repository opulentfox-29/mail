FROM ubuntu
FROM python:3.9.2
WORKDIR /mail
COPY . /mail
RUN apt update
RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
RUN apt install -y ./google-chrome-stable_current_amd64.deb
RUN pip install -r /mail/requirements.txt --no-cache-dir
expose 8000
RUN python manage.py migrate
ENTRYPOINT ["python", "manage.py", "runserver", "0.0.0.0:8000"]