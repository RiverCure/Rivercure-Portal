from django.urls import path
from . import views 
from .views import (
    ContextListView, 
    ContextDetailView, 
    HydroFeatureCreateView, 
    HydroFeatureListView, 
    HydroFeatureUpdateView, 
    HydroFeatureDetailView,
    HydroFeatureDeleteView
)

urlpatterns = [
    path('', ContextListView.as_view(), name='rivercure-home'),
    path('context/<str:pk>', ContextDetailView.as_view(), name='context-detail'),
    path('about/', views.about, name='rivercure-about'),
    path('hydrofeatures/', HydroFeatureListView.as_view(), name='hydrofeature-list'),
    path('hydrofeature/<int:pk>', HydroFeatureDetailView.as_view(), name='hydrofeature-detail'),
    path('hydrofeature/new/', HydroFeatureCreateView.as_view(), name='hydrofeature-create'),
    path('hydrofeature/<int:pk>/update/', HydroFeatureUpdateView.as_view(), name='hydrofeature-update'),
    path('hydrofeature/<int:pk>/delete/', HydroFeatureDeleteView.as_view(), name='hydrofeature-delete'),

   
]