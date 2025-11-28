from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from api import serializers
from foodgram.settings import USER_SELFINFO_PATH

User = get_user_model()


class UserViewSet(ModelViewSet):
    serializer_class = serializers.UserSerializer
    queryset = User.objects.all()
    lookup_field = 'id'
    permission_classes = (AllowAny,)

    def get_permissions(self):
        if self.action in ('list', 'retrieve', 'create'):
            return (AllowAny(),)
        return (IsAuthenticated(),)

    @action(methods=['GET'], detail=False, url_path=USER_SELFINFO_PATH)
    def me(self, request):
        serializer = serializers.UserSerializer(request.user)
        return Response(serializer.data)

    @action(
        methods=['PUT', 'DELETE'],
        detail=False,
        url_path=USER_SELFINFO_PATH + '/avatar',
    )
    def avatar(self, request): ...

    @action(methods=['GET'], detail=False)
    def subscriptions(self, request): ...

    @action(methods=['PUT'], detail=True)
    def subscribe(self, request, id=None):
        author = User.get_object_or_404(id=id)
        subscription = serializers.CreateSubscriptionSerializer(
            data={'author': author, 'user': request.user}
        )
        subscription.is_valid(raise_exception=True)
        subscription.save()
        return Response(status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, id=None): ...
