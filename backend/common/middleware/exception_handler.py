"""
Custom exception handler for DRF API responses.
"""
from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework import status
from rest_framework.response import Response


def custom_exception_handler(exc, context):
    """
    Custom exception handler that returns standardized error responses.
    """
    response = drf_exception_handler(exc, context)

    if response is not None:
        # DRF exception
        error_response = {
            "success": False,
            "message": str(exc),
            "errors": response.data if isinstance(response.data, dict) else {},
        }
        response.data = error_response
    else:
        # Non-DRF exception
        response = Response(
            {
                "success": False,
                "message": "An unexpected error occurred.",
                "errors": {"detail": str(exc)},
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return response
