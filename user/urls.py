from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CustomerViewSet, CourtTypeViewSet, CourtViewSet,
    PriceTableViewSet, PriceTableCourtViewSet,
    PriceTableTimeSlotViewSet, BookingViewSet, QLDonDatViewSet
)


router = DefaultRouter()
router.register(r'customers', CustomerViewSet)
router.register(r'court-types', CourtTypeViewSet)
router.register(r'courts', CourtViewSet)
router.register(r'price-tables', PriceTableViewSet)
router.register(r'price-table-courts', PriceTableCourtViewSet)
router.register(r'price-table-time-slots', PriceTableTimeSlotViewSet)
router.register(r'bookings', BookingViewSet)
router.register(r'QL_DonDat', QLDonDatViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
