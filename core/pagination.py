from rest_framework.pagination import PageNumberPagination

class ImagenOCRPagination(PageNumberPagination):
    page_size = 1

class EjercicioAlumnoPagination(PageNumberPagination):
    page_size = 1
    page_size_query_param = 'page_size'