from django.urls import path, include
from .views import show_context, download_context, ContextViewSet, UploadContext
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'context', ContextViewSet)

urlpatterns = [
    path('', show_context, name='context_manage'),
    path('upload/', UploadContext.as_view(), name='context_upload'),
    path('download/<str:context_code>', download_context, name='download_context'),
    path('api/', include(router.urls)),
]