from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PriceTableViewSet, PriceTableCourtViewSet, PriceTableTimeSlotViewSet

router = DefaultRouter()
router.register(r'price-tables', PriceTableViewSet)
router.register(r'price-table-courts', PriceTableCourtViewSet)
router.register(r'price-table-time-slots', PriceTableTimeSlotViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
