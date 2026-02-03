from django.shortcuts import redirect
from rest_framework.views import APIView


class ShortLinkView(APIView):
    def get(self, request, recipe_id):
        return redirect(f'/recipes/{recipe_id}/')
