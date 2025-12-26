from http import HTTPStatus

import pytest
from pytest_lazyfixture import lazy_fixture

ANONYM_CLIENT = lazy_fixture('anonym_client')
AUTHOR_CLIENT = lazy_fixture('author_client')
READER_CLIENT = lazy_fixture('user_client')
USER_POST_LOGIN_URL = lazy_fixture('users_login_url')
USER_SELFINFO_URL = lazy_fixture('users_selfinfo_url')
USER_LIST_URL = lazy_fixture('users_list_url')
USER_PROFILE_URL = lazy_fixture('users_profile_url')
USER_PUT_AVATAR_URL = lazy_fixture('users_avatar_url')
USER_GET_SUBSCRIPTION_URL = lazy_fixture('users_get_subscriptions_url')
USER_POST_SUBSCRIPTION_URL = lazy_fixture('users_post_subscriptions_url')
USER_POST_PASSWORD_URL = lazy_fixture('users_set_password_url')
RECIPE_LIST_URL = lazy_fixture('recipes_list_url')
RECIPE_DETAIL_URL = lazy_fixture('recipes_detail_url')
RECIPE_POST_FAVORITES_URL = lazy_fixture('favorite_url')
RECIPE_POST_SHOPPING_CART_URL = lazy_fixture('shopping_cart_url')

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    'client_fixture, url, expected_status',
    (
        # Анонимный пользователь
        (ANONYM_CLIENT, USER_SELFINFO_URL, HTTPStatus.UNAUTHORIZED),
        (ANONYM_CLIENT, USER_LIST_URL, HTTPStatus.OK),
        (ANONYM_CLIENT, USER_PROFILE_URL, HTTPStatus.OK),
        (ANONYM_CLIENT, USER_GET_SUBSCRIPTION_URL, HTTPStatus.UNAUTHORIZED),
        (ANONYM_CLIENT, RECIPE_LIST_URL, HTTPStatus.OK),
        (ANONYM_CLIENT, RECIPE_DETAIL_URL, HTTPStatus.OK),
        # Автор
        (AUTHOR_CLIENT, USER_SELFINFO_URL, HTTPStatus.OK),
        (AUTHOR_CLIENT, USER_LIST_URL, HTTPStatus.OK),
        (AUTHOR_CLIENT, USER_PROFILE_URL, HTTPStatus.OK),
        (AUTHOR_CLIENT, USER_GET_SUBSCRIPTION_URL, HTTPStatus.OK),
        (AUTHOR_CLIENT, RECIPE_LIST_URL, HTTPStatus.OK),
        (AUTHOR_CLIENT, RECIPE_DETAIL_URL, HTTPStatus.OK),
    ),
)
def test_control_get_method_status_codes(
    client_fixture,
    url,
    expected_status,
):
    # response = client_fixture.get(url)
    assert client_fixture.get(url).status_code == expected_status


@pytest.mark.skip(reason='В разработке')
@pytest.mark.parametrize(
    'client_fixture, url, expected_status',
    (
        (ANONYM_CLIENT, USER_POST_LOGIN_URL, HTTPStatus.OK),
        (ANONYM_CLIENT, USER_POST_SUBSCRIPTION_URL, HTTPStatus.UNAUTHORIZED),
        (ANONYM_CLIENT, USER_POST_PASSWORD_URL, HTTPStatus.UNAUTHORIZED),
        (ANONYM_CLIENT, RECIPE_POST_FAVORITES_URL, HTTPStatus.UNAUTHORIZED),
        (ANONYM_CLIENT, RECIPE_POST_SHOPPING_CART_URL, HTTPStatus.UNAUTHORIZED),
        (AUTHOR_CLIENT, USER_POST_SUBSCRIPTION_URL, HTTPStatus.OK),
        (AUTHOR_CLIENT, USER_POST_PASSWORD_URL, HTTPStatus.OK),
        (AUTHOR_CLIENT, RECIPE_POST_FAVORITES_URL, HTTPStatus.OK),
        (AUTHOR_CLIENT, RECIPE_POST_SHOPPING_CART_URL, HTTPStatus.OK),
    ),
)
def test_control_post_method_status_codes(
    client_fixture,
    url,
    expected_status,
):
    response = client_fixture.post(url)
    assert response.status_code == expected_status
