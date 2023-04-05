from django.db import models


class Proton(models.Model):
    login = models.CharField(max_length=150, blank=True)
    password = models.CharField(max_length=150, blank=True)
    duck_name = models.CharField(max_length=150, blank=True)
