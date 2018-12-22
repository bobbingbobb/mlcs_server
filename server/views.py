# -*- coding: utf-8 -*-
from django.contrib import auth
from django.shortcuts import render, redirect
from django.core.exceptions import ObjectDoesNotExist
from .models import GPU, Image, Port_in_use, Deployment, Counter, Cimage
from django.http import HttpResponse
from django.contrib.auth import authenticate, logout, login as server_login
from django.contrib.auth.models import User
import datetime
import os
import string
import re
import yaml
import time
from django.core.files import File


def index(request):
  user = request.user
  userown = ''

  #dashboard
  if str(user) != 'AnonymousUser':
    if Deployment.objects.filter(user=user).count() != 0:   #if the user has any container
      userown = Deployment.objects.filter(user=user)

  #select
  gpulist = GPU.objects.filter(used=False)
  imagelist = Image.objects.values('name').distinct()

  try:
    if request.COOKIES["restore"] != "None":
      restore = int(request.COOKIES["restore"])
    else:
      restore = 0
  except KeyError:
    restore = 0

  try:
    cname = Deployment.objects.get(id=restore)
    repo = str(user)+'-'+cname.name
    backup = Cimage.objects.filter(repo=repo)
  except ObjectDoesNotExist:
    backup = {}

  data = {'gpu':gpulist,'image':imagelist,'userown':userown,'restore':restore,'backup':backup}
  response = render(request, 'server/index.html',data)
  response.set_cookie('restore',0)

  return response












def select(request):
  #get data from database
  print("current time : " + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'))

  gpulist = GPU.objects.order_by('id')
  imagelist = Image.objects.values('name').distinct()
  error = []
  gpu_use = ''
  message = ''

  if request.method == 'POST':
    #get inputs
    user = request.user
    cname = request.POST.get('cname')
    gpuid = request.POST.getlist('gpuselect')
    ram = request.POST.get('ram')
    ram = int(ram)
    image = request.POST.get('imageselect')
    wrong = 0   #good or not

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

      with open('/home/nmg/webserver/yamlfiles/example.yaml', 'r') as f:
        y = yaml.load(f) #dict

        node = {}
        for g in gpuid:
          gpu = GPU.objects.get(id=g)
          gpu_use += str(gpu.id)
          gpu_use += '+'
          gpu.used = True
          gpu.save()
          node[gpu.label] = gpu.accel

        Deployment.objects.create(name=cname, user=user, ram=ram, image=Image.objects.get(name=image),port=port_now,gpu_inuse=gpu_use)
        free_mem.number -= ram
        free_mem.save()

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

      print("current time : " + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'))
      print(gpu_use)

      return redirect('index')


  data = {'gpu':gpulist,'image':imagelist,'error':error,'message':message}

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

    tag = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')    #docker image tag cannot contain ":"
    print(tag)
    repo = user+"-"+save

    deployment = Deployment.objects.get(name=save, user=request.user)
    deployment.backup = True
    deployment.save()
    Cimage.objects.create(repo=repo, tag=tag)

    repotag = repo+":"+tag
    os.system("ssh ctaserver docker commit "+cid+" "+repotag)
    os.system("ssh ctaserver docker save -o /home/nmg/saves/"+repo+"-"+tag+".tar "+repotag)
    os.system("ssh ctaserver docker image rm "+repotag)

    data = {'save':save}
    return redirect('index')


  return render(request, 'server/save.html',data)

def restore(request):
  if request.method == 'POST':
    response = redirect('index')
    response.set_cookie('restore',request.POST.get('btn_restore'))

    return response

def load(request):
  user = request.user
  data = {}

  if request.method == 'POST':
    load = request.POST.get('tarselect')
    repo_tag = load.split('+')

    os.system("kubectl delete deployment "+repo_tag[0])
    os.system("kubectl delete svc "+repo_tag[0])
    time.sleep(15)

    tarname = load.replace('+','-')
    os.system("ssh ctaserver docker load -i /home/nmg/saves/"+tarname+".tar")

    u_name = repo_tag[0].split('-')
    deployment = Deployment.objects.get(name=u_name[1], user=user)
    os.system("kubectl run "+repo_tag[0]+" --image="+repo_tag[0]+":"+repo_tag[1])

    port = str(deployment.port)
    os.system("kubectl expose deploy " +repo_tag[0]+ " --type LoadBalancer --external-ip=140.128.101.13 --port "+port+" --target-port 22")

  return redirect('index')

def delete(request):
  if request.method == 'POST':
    cname = request.POST.get('btn_del')
    user = request.user
    ram = Counter.objects.get(name='free_mem')

    deployment = Deployment.objects.get(name=cname, user=user)
    free_mem = Counter.objects.get(name='free_mem')
    free_mem.number += deployment.ram
    user = str(user)
    repo = user+"-"+cname
    backup = Cimage.objects.filter(repo=repo)
    dg = deployment.gpu_inuse
    gpu_use = dg.split('+')
    gpu_use.pop()
    print(gpu_use)
    print(type(gpu_use))
    for g in gpu_use:
      gpu = GPU.objects.get(id=int(g))
      gpu.used = False
      gpu.save()
    for b in backup:
      b.delete()
    deployment.delete()
    free_mem.save()

    os.system("kubectl delete deployment "+user+"-"+cname)

    return redirect('index')

def blank(request):

  response = render(request, 'server/blank.html')
  response.set_cookie('test',7777)
  return response

def sign(request):
  if request.method == 'POST':
    form = auth.forms.UserCreationForm(request.POST)    #authenticate username and passwd

    if form.is_valid():
      form.save()   #create a user object and store into db
      username = form.cleaned_data['username']
      password = form.cleaned_data['password1']
      user = authenticate(username=username, password=password)
      server_login(request, user)   #login
      return redirect('index')

  else:
    form = auth.forms.UserCreationForm()    #using usercreate middleware

  data = {'text':form}  #pass the special form to html
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
