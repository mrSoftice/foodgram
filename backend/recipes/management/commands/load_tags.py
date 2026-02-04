from recipes.management.commands._importers import BaseImportCommand
from recipes.models import Tag


class Command(BaseImportCommand):
    model = Tag
    filename_stem = 'tags'
