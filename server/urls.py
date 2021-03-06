from django.urls import path
from . import views

urlpatterns = [
  path('', views.index, name='index'),
  path('select/', views.select, name='select'),
  path('respond/', views.respond, name='respond'),
  path('sign/', views.sign, name='sign'),
  #path('login/', views.login, name='login'),
  #path('logout/', views.logout, name='logout'),
  path('save/', views.save, name='save'),
  path('blank/', views.blank, name='blank'),
]
