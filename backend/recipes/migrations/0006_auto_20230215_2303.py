# Generated by Django 3.2.17 on 2023-02-15 22:03

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0005_remove_favorite_user_to_recipe_favorite'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='follow',
            options={},
        ),
        migrations.RemoveConstraint(
            model_name='follow',
            name='user_to_author_follow',
        ),
        migrations.RemoveConstraint(
            model_name='follow',
            name='following_himself',
        ),
    ]