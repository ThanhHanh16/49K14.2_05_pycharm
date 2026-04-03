from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CustomerViewSet
from rest_framework.routers import DefaultRouter
from .views import LoaiSanViewSet, SanViewSet, BangGiaViewSet


router = DefaultRouter()
router.register(r'customers', CustomerViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
]

router = DefaultRouter()
router.register(r'loai-san', LoaiSanViewSet, basename='loai-san')
router.register(r'san', SanViewSet, basename='san')
router.register(r'bang-gia', BangGiaViewSet, basename='bang-gia')

urlpatterns = router.urls