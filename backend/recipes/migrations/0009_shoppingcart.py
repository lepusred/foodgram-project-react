# Generated by Django 3.2.17 on 2023-02-17 00:23

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('recipes', '0008_favorite_user_to_recipe_favorite'),
    ]

    operations = [
        migrations.CreateModel(
            name='ShoppingCart',
            fields=[
                ('id', models.AutoField(auto_created=True,
                 primary_key=True, serialize=False, verbose_name='ID')),
                ('recipe',
                 models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                   related_name='selected_recipe_cart',
                                   to='recipes.recipe')),
                ('user',
                 models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                   related_name='selector_cart',
                                   to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Список покупок',
                'verbose_name_plural': 'Список покупок',
            },
        ),
    ]
