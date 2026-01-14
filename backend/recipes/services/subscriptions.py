from django.db.models import BooleanField, Exists, OuterRef, Value
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import NotAuthenticated, ValidationError

from recipes.models import Subscription, User
from recipes.services import core


def annotate_is_subscribed(user_qs, current_user):
    """
    Добавляет поле is_subscribed к queryset пользователей.
    Если пользователь анонимный — ставим False без подзапроса.
    """
    if not current_user or current_user.is_anonymous:
        return user_qs.annotate(
            is_subscribed=Value(False, output_field=BooleanField())
        )
    return user_qs.annotate(
        is_subscribed=Exists(
            Subscription.objects.filter(
                user=current_user, author=OuterRef('pk')
            )
        )
    )


def get_author_or_404(author_id):
    return get_object_or_404(User, id=author_id)


def subscribe(user, author):
    """
    Создает подписку на автора.
    Возвращает:
      - Subscription (успех)
      - Поднимает исключение ValidationError (ошибка)
    """
    if user.is_anonymous:
        raise NotAuthenticated(detail=core.ERROR_UNAUTHORIZED)

    if user == author:
        raise ValidationError(core.ERROR_SELF_SUBSCRIPTION)

    subscription, created = core.get_or_create_model_instance(
        Subscription,
        user=user,
        author=author,
    )
    if not created:
        raise ValidationError(core.ERROR_ALREADY_SUBSCRIBED)
    return subscription


def unsubscribe(user, author):
    """Удаляет подписку на автора.
    Возвращает:
      - None (успех)
      - Response (ошибка)
    """
    if user.is_anonymous:
        raise NotAuthenticated(core.ERROR_UNAUTHORIZED)

    if user == author:
        # это спорно, но логично держать единое правило
        raise ValidationError(core.ERROR_SELF_SUBSCRIPTION)

    deleted_count, _ = Subscription.objects.filter(
        user=user,
        author=author,
    ).delete()
    if deleted_count == 0:
        raise ValidationError(core.ERROR_NOT_SUBSCRIBED)
    return None
