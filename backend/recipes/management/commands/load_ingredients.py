import os
import json

from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    def handle(self, *args, **options):
        Ingredient.objects.all().delete()
        file_path = os.path.join(settings.BASE_DIR, 'data/ingredients.json')

        with open(file_path, 'r', encoding='utf-8', ) as file:
            data = json.load(file)
            for element in data:
                Ingredient.objects.create(
                    name=element.get('name'),
                    measurement_unit=element.get('measurement_unit')
                )
