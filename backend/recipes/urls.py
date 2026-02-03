from django.urls import path

from .views import ShortLinkView

urlpatterns = [
    path('', ShortLinkView.as_view(), name='short-link-view'),
]
