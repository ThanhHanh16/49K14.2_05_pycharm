from django.urls import path

from .views import (
    AdminOnlyAPIView,
    LoginAPIView,
    ProfileAPIView,
    ProfileUpdateAPIView,
    RegisterAPIView,
)

urlpatterns = [
    path("register/", RegisterAPIView.as_view(), name="register"),
    path("login/", LoginAPIView.as_view(), name="login"),
    path("profile/", ProfileAPIView.as_view(), name="profile"),
    path("profile/update/", ProfileUpdateAPIView.as_view(), name="profile-update"),
    path("admin-only/", AdminOnlyAPIView.as_view(), name="admin-only"),
]
