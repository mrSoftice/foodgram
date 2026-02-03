import pytest

from recipes.models import ShoppingCart


@pytest.mark.django_db
def test_get_link_returns_short_link(user_client, recipe1, get_short_link_url):
    response = user_client.get(get_short_link_url)

    assert response.status_code == 200
    assert response.data['short-link'] == (
        # f'http://testserver/s/{encode_hashid(recipe1.id)}'
        f'http://testserver/s/{recipe1.id}/'
    )


@pytest.mark.django_db
def test_shopping_cart_requires_auth(anonym_client, shopping_cart_url):
    response = anonym_client.post(shopping_cart_url)

    assert response.status_code == 401


@pytest.mark.django_db
def test_shopping_cart_add_and_remove(
    user_client, user, recipe1, shopping_cart_url
):
    add_response = user_client.post(shopping_cart_url)

    assert add_response.status_code == 201
    assert ShoppingCart.objects.filter(user=user, recipe=recipe1).exists()

    delete_response = user_client.delete(shopping_cart_url)

    assert delete_response.status_code == 204
    assert not ShoppingCart.objects.filter(user=user, recipe=recipe1).exists()


@pytest.mark.django_db
def test_shopping_cart_rejects_duplicate(user_client, shopping_cart_url):
    first_response = user_client.post(shopping_cart_url)
    second_response = user_client.post(shopping_cart_url)

    assert first_response.status_code == 201
    assert second_response.status_code == 400
