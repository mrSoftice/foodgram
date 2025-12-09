from rest_framework.pagination import LimitOffsetPagination


class PageLimitPagination(LimitOffsetPagination):
    page_size_query_param = 'limit'
    page_query_param = 'page'
    default_limit = 10
    max_page_size = 100

    def get_offset(self, request):
        return 0
