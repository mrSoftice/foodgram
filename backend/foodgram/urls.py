from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic import TemplateView

MEDIA_URL = settings.MEDIA_URL
MEDIA_ROOT = settings.MEDIA_ROOT

app_name = 'foodgram'

urlpatterns = [
    path('api/', include('api.urls')),
    path('admin/', admin.site.urls, name='admin'),
    # path('s/<int:recipe_id>/', include('recipes.urls')),
    path('', include('recipes.urls')),
]


urlpatterns += static(MEDIA_URL, document_root=MEDIA_ROOT)

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
        re_path(
            r'^(?!api/).*', TemplateView.as_view(template_name='index.html')
        ),
    ]
