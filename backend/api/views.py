from django.contrib.auth import get_user_model
from djoser.views import UserViewSet as BaseUserViewSet
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny

from api import serializers

User = get_user_model()


class UserViewSet(BaseUserViewSet):
    serializer_class = serializers.UserSerializer
    queryset = User.objects.all()
    permission_classes = (AllowAny,)

    @action(methods=['GET'], detail=False)
    def subscriptions(self, request): ...

    @action(url_path='me/avatar', methods=['PUT', 'DELETE'], detail=True)
    def avatar(self, request): ...

    @action(methods=['PUT'], detail=True)
    def subscribe(self, request, id=None): ...

    @subscribe.mapping.delete
    def unsubscribe(self, request, id=None): ...
