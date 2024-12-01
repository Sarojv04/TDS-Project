# Generated by Django 5.1.3 on 2024-11-21 23:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('surveys', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='survey',
            name='is_published',
        ),
        migrations.AddField(
            model_name='survey',
            name='status',
            field=models.CharField(choices=[('draft', 'Draft'), ('published', 'Published')], default='draft', max_length=10),
        ),
        migrations.AddField(
            model_name='survey',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
