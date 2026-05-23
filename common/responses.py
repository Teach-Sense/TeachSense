"""
Standardized API response format for all endpoints.
"""
from rest_framework.response import Response
from rest_framework import status as http_status


class APIResponse:
    """Standardized response wrapper for API endpoints."""

    @staticmethod
    def success(data=None, message="Success", status_code=http_status.HTTP_200_OK):
        """Return successful response."""
        return Response(
            {
                "success": True,
                "message": message,
                "data": data,
            },
            status=status_code,
        )

    @staticmethod
    def error(
        message="Error",
        status_code=http_status.HTTP_400_BAD_REQUEST,
        errors=None,
    ):
        """Return error response."""
        return Response(
            {
                "success": False,
                "message": message,
                "errors": errors or {},
            },
            status=status_code,
        )

    @staticmethod
    def created(data=None, message="Created successfully"):
        """Return 201 created response."""
        return APIResponse.success(
            data=data,
            message=message,
            status_code=http_status.HTTP_201_CREATED,
        )

    @staticmethod
    def no_content(message="Deleted successfully"):
        """Return 204 no content response."""
        return Response(
            {
                "success": True,
                "message": message,
            },
            status=http_status.HTTP_204_NO_CONTENT,
        )

    @staticmethod
    def unauthorized(message="Unauthorized access"):
        """Return 401 unauthorized response."""
        return APIResponse.error(
            message=message,
            status_code=http_status.HTTP_401_UNAUTHORIZED,
        )

    @staticmethod
    def forbidden(message="Access denied"):
        """Return 403 forbidden response."""
        return APIResponse.error(
            message=message,
            status_code=http_status.HTTP_403_FORBIDDEN,
        )

    @staticmethod
    def not_found(message="Resource not found"):
        """Return 404 not found response."""
        return APIResponse.error(
            message=message,
            status_code=http_status.HTTP_404_NOT_FOUND,
        )

    @staticmethod
    def conflict(message="Resource conflict"):
        """Return 409 conflict response."""
        return APIResponse.error(
            message=message,
            status_code=http_status.HTTP_409_CONFLICT,
        )

    @staticmethod
    def validation_error(errors, message="Validation failed"):
        """Return 400 validation error response."""
        return APIResponse.error(
            message=message,
            status_code=http_status.HTTP_400_BAD_REQUEST,
            errors=errors,
        )
