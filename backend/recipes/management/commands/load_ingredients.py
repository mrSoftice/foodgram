from recipes.models import Ingredient

from ._importers import BaseImportCommand


class Command(BaseImportCommand):
    model = Ingredient
    filename_stem = 'ingredients'
    unique_fields = ('name', 'measurement_unit')
