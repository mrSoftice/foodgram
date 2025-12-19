from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from foodgram import settings
from recipes.views import short_recipe_redirect

urlpatterns = [
    path('api/', include('api.urls')),
    path('admin/', admin.site.urls),
    path('s/<str:code>/', short_recipe_redirect, name='short-recipe-link'),
]


urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [path('__debug__/', include(debug_toolbar.urls))]
