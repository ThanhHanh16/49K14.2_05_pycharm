from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import reset_password_quick
from customers.views import CustomerViewSet
from courts.views import CourtTypeViewSet, CourtViewSet
from pricing.views import PriceTableViewSet, PriceTableCourtViewSet, PriceTableTimeSlotViewSet
from bookings.views import BookingViewSet, QLDonDatViewSet, DashboardStatsAPIView

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
    path('dashboard-stats/', DashboardStatsAPIView.as_view(), name='dashboard-stats'),
    path('reset-password/', reset_password_quick, name='reset-password'),
]
