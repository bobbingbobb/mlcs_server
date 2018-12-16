from django.contrib import admin

# Register your models here.
from .models import GPU, Image, Port_in_use, Deployment, Counter, Cimage

admin.site.register(GPU)
admin.site.register(Image)
admin.site.register(Port_in_use)
admin.site.register(Deployment)
admin.site.register(Counter)
admin.site.register(Cimage)
