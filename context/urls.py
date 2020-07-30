from django.urls import path, include
from . import views 
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'context', views.ContextViewSet)

urlpatterns = [
    path('', views.show_context, name='context'),
    path('download/', views.download_context, name='download_context'),
    path('api/', include(router.urls))
]