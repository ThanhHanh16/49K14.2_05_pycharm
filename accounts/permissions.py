from rest_framework.permissions import BasePermission


class IsCustomer(BasePermission):
    def has_permission(self, request, view):
        profile = getattr(request.user, "customer_profile", None)
        return bool(request.user and request.user.is_authenticated and profile and profile.role == "customer")


class IsStaffOrAdmin(BasePermission):
    def has_permission(self, request, view):
        profile = getattr(request.user, "customer_profile", None)
        return bool(
            request.user
            and request.user.is_authenticated
            and (
                request.user.is_staff
                or request.user.is_superuser
                or (profile and profile.role in ["staff", "admin"])
            )
        )

