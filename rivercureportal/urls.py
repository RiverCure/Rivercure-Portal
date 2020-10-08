from django.urls import path
from . import views 
from .views import (
    HydroFeatureCreateView, 
    HydroFeatureListView, 
    HydroFeatureUpdateView, 
    HydroFeatureDetailView,
    HydroFeatureDeleteView,
    home,
    users,
)

urlpatterns = [
    path('', home, name='rivercure-home'),
    path('about/', views.about, name='rivercure-about'),
    path('hydrofeatures/', HydroFeatureListView.as_view(), name='hydrofeature-list'),
    path('hydrofeature/<int:pk>', HydroFeatureDetailView.as_view(), name='hydrofeature-detail'),
    path('hydrofeature/new/', HydroFeatureCreateView.as_view(), name='hydrofeature-create'),
    path('hydrofeature/<int:pk>/update/', HydroFeatureUpdateView.as_view(), name='hydrofeature-update'),
    path('hydrofeature/<int:pk>/delete/', HydroFeatureDeleteView.as_view(), name='hydrofeature-delete'),
    path('hydrofeatures/', HydroFeatureListView.as_view(), name='hydrofeature-list'),
    path('users/', users, name='users'),
    
   
]