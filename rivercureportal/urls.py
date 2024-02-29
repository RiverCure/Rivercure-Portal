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
    ProfileDetailView,
    clearNotifications,
    UserUpdateView,
    NotificationListView,
    about
)

urlpatterns = [
    path('', home, name='rivercure-home'),
    path('hydrofeatures/', HydroFeatureListView.as_view(), name='hydrofeature-list'),
    path('hydrofeature/<int:pk>', HydroFeatureDetailView.as_view(), name='hydrofeature-detail'),
    path('hydrofeature/new/', HydroFeatureCreateView.as_view(), name='hydrofeature-create'),
    path('hydrofeature/<int:pk>/update/', HydroFeatureUpdateView.as_view(), name='hydrofeature-update'),
    path('hydrofeature/<int:pk>/delete/', HydroFeatureDeleteView.as_view(), name='hydrofeature-delete'),
    path('users/', users, name='users'),
    path('profile/<int:pk>', ProfileDetailView.as_view(), name='profile-detail'),
    path('profile/<int:pk>/update', UserUpdateView.as_view(), name='profile-update'),
    path('notification/clear', clearNotifications, name='notifications-clear'),
    path('notification/all', NotificationListView.as_view(), name='notifications-all'),
    path('about/', about, name='rivercure-about')
]
