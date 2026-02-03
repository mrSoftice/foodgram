from rest_framework import status
from rest_framework.response import Response

ERROR_UNAUTHORIZED = {'detail': 'Учетные данные не были предоставлены.'}

ERROR_RECIPE_NOT_IN_LIST = {'detail': 'Рецепт {recipe} не найден в {list}.'}
ERROR_RECIPE_IN_LIST = {'detail': 'Рецепт {recipe} уже есть в {list}.'}

ERROR_SELF_SUBSCRIPTION = {'author': 'Нельзя подписаться на самого себя.'}
ERROR_ALREADY_SUBSCRIBED = {'detail': 'Вы уже подписаны на  автора {author}.'}
ERROR_NOT_SUBSCRIBED = {'detail': 'Вы не подписаны на автора {author}.'}

ERROR_BAD_FORMAT = {'file_format': 'Неподдерживаемый формат файла.'}

SUCCESS_DELETED_RESPONSE = Response(status=status.HTTP_204_NO_CONTENT)


def format_error(template: dict, **kwargs) -> dict:
    return {
        k: (v.format(**kwargs) if isinstance(v, str) else v)
        for k, v in template.items()
    }
