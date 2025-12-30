from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAuthorOrReadOnly(BasePermission):
    """Доступ на Чтение для всех, Изменение доступно только авторам.

    - SAFE_METHODS (GET, HEAD, OPTIONS) разрешены для всех запросов.
    - POST разрешены только аутентифицированным пользователям.
    - PUT/PATCH/DELETE разрешены только авторам рецептов.
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        # создание и удаление (POST, DELETE) доступно только аутентифицированным
        # пользователям
        if request.method == 'POST':
            return request.user and request.user.is_authenticated
        # остальные методы (PUT, PATCH, DELETE) мы передаем
        # в has_object_permission
        return True

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        author = getattr(obj, 'author', None)
        if author is None:
            return False
        return (
            request.user
            and request.user.is_authenticated
            and author == request.user
        )
