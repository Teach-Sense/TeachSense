"""
Custom permission classes for API endpoints.
"""
from rest_framework import permissions
from apps.users.models import User


class IsLecturer(permissions.BasePermission):
    """
    Permission to allow only lecturers.
    """

    message = "Only lecturers can access this resource."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "lecturer"
        )


class IsStudent(permissions.BasePermission):
    """
    Permission to allow only students.
    """

    message = "Only students can access this resource."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "student"
        )


class IsLecturerOrStudent(permissions.BasePermission):
    """
    Permission to allow any authenticated user (lecturer or student).
    """

    message = "This resource is only available to authenticated users."

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated


class IsSessionOwner(permissions.BasePermission):
    """
    Permission to allow only the lecturer who created the session.
    """

    message = "You do not have permission to access this session."

    def has_object_permission(self, request, view, obj):
        # obj is a Session
        return (
            request.user
            and request.user.is_authenticated
            and obj.lecturer.user == request.user
        )


class IsQuestionOwner(permissions.BasePermission):
    """
    Permission to allow access only to questions in sessions the user owns/can access.
    """

    message = "You do not have permission to access this question."

    def has_object_permission(self, request, view, obj):
        # obj is a Question
        return (
            request.user
            and request.user.is_authenticated
            and (
                obj.session.lecturer.user == request.user
                or request.user in obj.session.enrolled_students.all()
            )
        )


class IsResponseOwner(permissions.BasePermission):
    """
    Permission to allow only the student who submitted the response.
    """

    message = "You do not have permission to access this response."

    def has_object_permission(self, request, view, obj):
        # obj is a Response
        return (
            request.user
            and request.user.is_authenticated
            and obj.student == request.user
        )


class IsDeviceAuthenticated(permissions.BasePermission):
    """
    Permission for device-to-server authentication via device token.
    """

    message = "Invalid or missing device token."

    def has_permission(self, request, view):
        device_token = request.META.get("HTTP_X_DEVICE_TOKEN")
        if not device_token:
            return False

        from apps.devices.models import Device

        try:
            device = Device.objects.get(device_token=device_token)
            request.device = device
            return True
        except Device.DoesNotExist:
            return False


class IsSuperUserOrReadOnly(permissions.BasePermission):
    """
    Permission to allow only superusers to edit, but allow read access to anyone.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_superuser
