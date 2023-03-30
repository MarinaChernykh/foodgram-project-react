from rest_framework.pagination import PageNumberPagination


class CustomPagination(PageNumberPagination):
    """Кастомизация пагинации для пользователей, рецептов."""

    page_size_query_param = 'limit'
