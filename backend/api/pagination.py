from rest_framework import pagination


class CustomPagination(pagination.PageNumberPagination):
    page_size = 6
    page_query_param = 'page'
    page_size_query_param = 'limit'
    max_page_size = 100


class CartPagination(pagination.LimitOffsetPagination):
    default_limit = 6
    page_query_param = 'page'
    page_size_query_param = 'limit'
    max_limit = 1000
