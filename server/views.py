# -*- coding: utf-8 -*-
from django.contrib import auth
from django.shortcuts import render, redirect
from django.core.exceptions import ObjectDoesNotExist
from .models import GPU, Image, Port_in_use, Deployment, Counter
from django.http import HttpResponse
from django.contrib.auth import authenticate, logout, login as server_login
from django.contrib.auth.models import User
import datetime
import os
import string
import re
import yaml
from django.core.files import File


def index(request):
  user = request.user
  userown = ''

  if str(user) != 'AnonymousUser':
    userown = Deployment.objects.filter(user=user)
    for k in userown:
      k.status = 'on' if k.status == True else 'off'

  #select
  gpulist = GPU.objects.order_by('id')
  imagelist = Image.objects.values('name').distinct()




  data = {'gpu':gpulist,'image':imagelist,'userown':userown}




  response = render(request, 'server/index.html',data)

  return response












def select(request):
  #get data from database
  print("current time : " + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'))

  gpulist = GPU.objects.order_by('id')
  imagelist = Image.objects.values('name').distinct()
  error = []

  if request.method == 'POST':
    #get inputs
    user = request.user
    cname = request.POST.get('cname')
    gpuid = request.POST.getlist('gpuselect')
    ram = request.POST.get('ram')
    ram = int(ram)
    image = request.POST.get('imageselect')
    wrong = 0   #good or not

    #textbox filled check
    '''
    if len(gpuid) == 0:
      error.append('please choose GPUs')
      wrong = 1
    '''
    if ram <= 0:
      error.append('please import some number meaningful')
      wrong = 1

    #same name check
    try:
      deployment = Deployment.objects.get(name=cname)   #if same name
      if user == deployment.user:   #if name is used by same user (same name but different user is okay)
        error.append('\''+cname+'\' has been used!')
        wrong = 1
    except ObjectDoesNotExist:
      pass

    #ram check
    free_mem = Counter.objects.get(name='free_mem')
    if free_mem.number < ram:
      error.append('no enough memory left!\nfree memory : '+str(free_mem.number)+' Gb')
      wrong == 1

    #everything's good
    if wrong == 0:
      usage = Port_in_use.objects.get(used='0')
      port_now = usage.port
      port_next = str(int(usage.port) + 1)

      Deployment.objects.create(name=cname, user=user, ram=ram, image=Image.objects.get(name=image),port=port_now)
      free_mem.number -= ram
      #free_mem.save()

      with open('/home/nmg/webserver/yamlfiles/example.yaml', 'r') as f:
        y = yaml.load(f) #dict

        node = {}
        for g in gpuid:
          gpu = GPU.objects.get(id=g)
          node[gpu.label] = gpu.accel
        y['spec']['template']['spec']['nodeSelector'] = node

        uplusname = str(user)+"-"+cname
        y['metadata']['name'] = uplusname
        y['spec']['selector']['matchLabels']['app'] = uplusname
        y['spec']['template']['spec']['containers'][0]['name'] = uplusname
        y['spec']['template']['metadata']['labels']['app'] = uplusname
        y['spec']['template']['spec']['containers'][0]['image'] = image
        y['spec']['template']['spec']['containers'][0]['resources']['limits']['memory'] = str(ram) + 'Gi'
        y['spec']['template']['spec']['containers'][0]['resources']['limits']['nvidia.com/gpu'] = len(gpuid)
        y['spec']['template']['spec']['containers'][0]['resources']['requests']['memory'] = str(ram/2) + 'Gi'


        with open('/home/nmg/webserver/yamlfiles/'+uplusname+'.yaml', 'w') as e:
          yaml.dump(y,e)

      os.system("kubectl create -f /home/nmg/webserver/yamlfiles/"+uplusname+".yaml")
      os.system("kubectl expose deploy " +uplusname+ " --type LoadBalancer --external-ip=140.128.101.13 --port "+port_now +" --target-port 22")

      usage.used = True

      Port_in_use.objects.create(port=port_next)
      usage.save()
      '''
      gpu.save()
      '''
      print("current time : " + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'))

      return redirect('index')


  data = {'gpu':gpulist,'image':imagelist,'error':error}

  return render(request, 'server/select.html',data)

def respond(request):

  return render(request, 'server/respond.html')

def save(request):
  user = request.user
  data = {}

  if request.method == 'POST':
    save = request.POST.get('btn_sav')
    user = str(user)
    savestr = "k8s_" + user + "-" + save + "_"

    k = os.popen("ssh ctaserver docker ps -aqf name="+savestr)
    cid = k.read(12)
    k.close()
    print(cid)

    date = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')    #docker image tag cannot contain ":"
    print(date)
    uplusname = user+"-"+save

    os.system("ssh ctaserver docker commit "+cid+" "+uplusname+":"+date)
    os.system("ssh ctaserver docker save -o /home/nmg/saves/"+uplusname+"-"+date+".tar "+uplusname+":"+date)

    data = {'save':save}
    return redirect('index')

  return render(request, 'server/save.html',data)

def blank(request):

  response = render(request, 'server/blank.html')
  response.set_cookie('test',7777)
  return response

def sign(request):
  if request.method == 'POST':
    form = auth.forms.UserCreationForm(request.POST)

    if form.is_valid():
      form.save()
      username = form.cleaned_data['username']
      password = form.cleaned_data['password1']
      user = authenticate(username=username, password=password)
      server_login(request, user)
      return redirect('index')

  else:
    form = auth.forms.UserCreationForm()

  data = {'text':form}
  print(data);
  return render(request, 'registration/sign.html', data)
'''
def login(request):
  return render(request, 'registration/login.html')
'''

'''
def logout(request):
  #logout(request)
  return logout(request)
'''
