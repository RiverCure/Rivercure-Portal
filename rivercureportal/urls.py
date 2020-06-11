from django.urls import path
from . import views 

urlpatterns = [
    path('', views.home, name='rivercure-home'),
    path('about/', views.about, name='rivercure-about'),

]