from recipes.management.commands._importers import BaseImportCommand
from recipes.models import Ingredient


class Command(BaseImportCommand):
    model = Ingredient
    filename_stem = 'ingredients'
