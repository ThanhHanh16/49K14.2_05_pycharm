from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CourtTypeViewSet, CourtViewSet

router = DefaultRouter()
router.register(r'court-types', CourtTypeViewSet)
router.register(r'courts', CourtViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
