from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import UserViewSet

v1_router = DefaultRouter()
v1_router.register(r'users', UserViewSet, basename='users')

urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path('', include('djoser.urls')),
]

# переопределяем пути djoser
urlpatterns += [
    path('', include(v1_router.urls)),
]
