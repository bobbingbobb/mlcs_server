from django.shortcuts import render
from .models import GPU, Image, User, Port_in_use
import os
#import string
import yaml
from django.core.files import File

def index(request):
  gpu = GPU.objects.order_by('id')

  for g in gpu:
    g.used = 'ready' if g.used == False else 'used'

  data = {'gpu':gpu}
  return render(request, 'server/index.html',data)

def select(request):
  gpu = GPU.objects.values('name').distinct()
  image = Image.objects.values('name').distinct()

  data = {'gpu':gpu,'image':image}

  return render(request, 'server/select.html',data)

def respond(request):
  
  gpuname = request.GET.get('gpuselect')
  gpu = GPU.objects.get(name=gpuname) 
  gpu.used = True if gpu.used == False else False

  with open('/home/nmg/yamlfiles/example1.yaml', 'r') as f:
    y = yaml.load(f) #dict
              
    if gpu.name=='Tesla_K20':
      select_gpu='nvidia-tesla-k20'
      y['spec']['template']['spec']['nodeSelector'] = dict(accelerator=select_gpu)
      y['metadata']['name'] = 'teslak20'
      expose = y['metadata']['name']
    elif gpu.name=='Tesla_K20x':
      select_gpu='nvidia-tesla-k20x'
      y['spec']['template']['spec']['nodeSelector'] = dict(accelerator2=select_gpu)
      y['metadata']['name'] = 'teslak20x'
      expose = y['metadata']['name']
    elif gpu.name=='Tesla_K620':
      select_gpu='nvidia-quadro-k620'
      y['spec']['template']['spec']['nodeSelector'] = dict(accelerator3=select_gpu)
      y['metadata']['name'] = 'quadrok620'
      expose = y['metadata']['name']
    
    with open('/home/nmg/yamlfiles/'+gpu.name+'.yaml', 'w') as e:
      yaml.dump(y,e) 
    
    usage = Port_in_use.objects.get(used='0')
    port_now = usage.port
    port_next = str(int(usage.port) + 1)

    os.system("kubectl create -f /home/nmg/yamlfiles/"+gpu.name+".yaml")
    os.system("kubectl expose deploy" + expose + "--type LoadBalancer --external-ip=140.128.101.13 --port"+port_now +" --target-port 22")

    usage.used = True if usage.used == False else False
    Port_in_use.objects.create(port=port_next)
    usage.save()
    gpu.save()


  data = {'gpu':gpu}

  return render(request, 'server/respond.html',data)

def sign(request):
  
  return render(request, 'server/sign.html')
