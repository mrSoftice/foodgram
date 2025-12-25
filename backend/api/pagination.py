from rest_framework.pagination import PageNumberPagination


class PageLimitPagination(PageNumberPagination):
    page_size_query_param = 'limit'
    page_query_param = 'page'
    default_limit = 6
    max_page_size = 100
