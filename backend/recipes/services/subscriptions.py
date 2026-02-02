from django.db.models import BooleanField, Exists, OuterRef, Value

from recipes.models import Subscription


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
