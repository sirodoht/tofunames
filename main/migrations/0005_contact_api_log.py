# Generated by Django 5.0.6 on 2024-06-02 15:50

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0004_alter_user_created_at"),
    ]

    operations = [
        migrations.AddField(
            model_name="contact",
            name="api_log",
            field=models.CharField(blank=True, max_length=1000, null=True),
        ),
    ]
