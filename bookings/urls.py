from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BookingViewSet, QLDonDatViewSet, DashboardStatsAPIView

router = DefaultRouter()
router.register(r'bookings', BookingViewSet)
router.register(r'QL_DonDat', QLDonDatViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard-stats/', DashboardStatsAPIView.as_view(), name='dashboard-stats'),
]
