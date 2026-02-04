from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAuthorOrReadOnly(BasePermission):
    """Доступ на Чтение для всех, Изменение доступно только авторам."""

    def has_object_permission(self, request, view, obj):
        return (request.method in SAFE_METHODS) or obj.author == request.user
