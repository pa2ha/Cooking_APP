import csv

from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):

    def handle(self, *args, **options):
        with open('data/ingredients.csv', 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                try:
                    item = None
                    item = Ingredient(name=row[0], measurement_unit=row[1])
                    item.full_clean()
                    item.save()
                    self.stdout.write(self.style.SUCCESS(
                        f"Запись для модели Ingredient успешно добавлена: {row}"))
                except Exception as error:
                    self.stdout.write(self.style.ERROR(
                            f'Ошибка в строке {row}: {error}'))
