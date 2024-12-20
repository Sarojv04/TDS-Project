# Generated by Django 5.1.3 on 2024-11-23 23:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('surveys', '0003_question_is_deleted_survey_is_deleted_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='option',
            options={'ordering': ['position']},
        ),
        migrations.AlterModelOptions(
            name='question',
            options={'ordering': ['position']},
        ),
        migrations.AddField(
            model_name='option',
            name='position',
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AddField(
            model_name='question',
            name='position',
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AddField(
            model_name='survey',
            name='archived',
            field=models.BooleanField(default=False),
        ),
    ]
