from recipes.models import Tag

from ._importers import BaseImportCommand


class Command(BaseImportCommand):
    model = Tag
    filename_stem = 'tags'
    unique_fields = ('name', 'slug')
