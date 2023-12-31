# Generated by Django 3.2.16 on 2023-11-27 13:21

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0002_auto_20231122_1241'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='recipe',
            options={'ordering': ('-pub_date',), 'verbose_name': 'рецепт', 'verbose_name_plural': 'Рецепты'},
        ),
        migrations.AlterModelOptions(
            name='shopping_cart',
            options={'ordering': ('user',), 'verbose_name': 'Список покупок', 'verbose_name_plural': 'Списки покупок'},
        ),
    ]
