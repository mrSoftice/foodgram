from rest_framework import status
from rest_framework.response import Response

ERROR_UNAUTHORIZED = {
    'errors': 'Авторизуйтесь для выполнения данного действия.'
}

ERROR_RECIPE_NOT_IN_LIST = {'errors': 'Рецепт не найден в списке.'}
ERROR_RECIPE_IN_LIST = {'errors': 'Рецепт уже есть в списке.'}

ERROR_SELF_SUBSCRIPTION = {'author': 'Нельзя подписаться на самого себя.'}
ERROR_ALREADY_SUBSCRIBED = {'errors': 'Вы уже подписаны на этого автора.'}
ERROR_NOT_SUBSCRIBED = {'errors': 'Вы не подписаны на этого автора'}

ERROR_EMPTY = {'errors': 'Список покупок пуст.'}
ERROR_BAD_FORMAT = {'file_format': 'Неподдерживаемый формат файла.'}

SUCCESS_DELETED_RESPONSE = Response(status=status.HTTP_204_NO_CONTENT)


def get_or_create_model_instance(model, defaults=None, **lookup):
    return model.objects.get_or_create(defaults=defaults, **lookup)
