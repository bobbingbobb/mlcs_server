from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

# Create your models here.
class GPU(models.Model):
  name = models.CharField(max_length=20)
  used = models.BooleanField(default=False)
  label = models.CharField(max_length=20, default='pending')
  vram = models.IntegerField(default=0)
  expose = models.CharField(max_length=20)
  accel = models.CharField(max_length=20, default="")

  def __str__(self):
    return '<ID : {}, GPU : {}, available : {}, label : {}, expose : {}, accel : {}>'.format(self.id, self.name, self.used, self.label, self.expose, self.accel)

class Image(models.Model):
  name = models.CharField(max_length=60)

  def __str__(self):
    return '<ID : {}, distro : {}>'.format(self.id, self.name)

class Port_in_use(models.Model):
  port = models.CharField(max_length=5)
  used = models.BooleanField(default=False)

  def __str__(self):
    return '<ID : {}, port : {}, used : {}>'.format(self.id, self.port, self.used)

class Deployment(models.Model):
  name = models.CharField(max_length=20)
  user = models.ForeignKey(User,on_delete=models.CASCADE, null=True)
  ram = models.IntegerField(default=0)
  image = models.ForeignKey(Image,on_delete=models.CASCADE, null=True)
  test = models.CharField(max_length=20, default='a')
  port = models.IntegerField(default=0)
  backup = models.BooleanField(default=False)

  def __str__(self):
    return '<ID : {}, name : {}, user : {}, ram : {}, image : {}, port : {}, backup : {}>'.format(self.id, self.name, self.user, self.ram, self.image, self.port, self.backup)

class Counter(models.Model):
  name = models.CharField(max_length=20)
  number = models.IntegerField(default=0)

  def __str__(self):
    return '<ID : {}, name : {}, number : {}>'.format(self.id, self.name, self.number)

class Cimage(models.Model):
  repo = models.CharField(max_length=50)
  tag = models.CharField(max_length=20)

  def __str__(self):
    return '<ID : {}, repo : {}, tag : {}>'.format(self.id, self.repo, self.tag)
