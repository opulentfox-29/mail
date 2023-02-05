from django.db import models


class Proton(models.Model):
    login = models.CharField(max_length=150)
    password = models.CharField(max_length=150)
    duck_name = models.CharField(max_length=150)
