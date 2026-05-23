"""
Pagination configuration for list endpoints.
"""
from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    """Standard pagination with 20 items per page."""

    page_size = 20
    page_size_query_param = "page_size"
    page_size_query_description = "Number of results to return per page."
    max_page_size = 100
    page_query_param = "page"
    page_query_description = "A page number within the paginated result set."

    def get_paginated_response(self, data):
        """Return paginated response with metadata."""
        return {
            "count": self.page.paginator.count,
            "next": self.get_next_link(),
            "previous": self.get_previous_link(),
            "page_size": self.page_size,
            "total_pages": self.page.paginator.num_pages,
            "current_page": self.page.number,
            "results": data,
        }


class LargeResultsSetPagination(PageNumberPagination):
    """Pagination with 100 items per page for large datasets."""

    page_size = 100
    page_size_query_param = "page_size"
    max_page_size = 500


class SmallResultsSetPagination(PageNumberPagination):
    """Pagination with 10 items per page for small datasets."""

    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50
