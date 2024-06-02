# Generated by Django 5.0.6 on 2024-06-02 17:02

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0006_contact_api_id"),
    ]

    operations = [
        migrations.CreateModel(
            name="Domain",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("domain_name", models.CharField(max_length=63)),
                (
                    "nameserver0",
                    models.CharField(blank=True, default="", max_length=253, null=True),
                ),
                (
                    "nameserver1",
                    models.CharField(blank=True, default="", max_length=253, null=True),
                ),
                (
                    "nameserver2",
                    models.CharField(blank=True, default="", max_length=253, null=True),
                ),
                (
                    "nameserver3",
                    models.CharField(blank=True, default="", max_length=253, null=True),
                ),
                ("api_log", models.CharField(blank=True, max_length=1000, null=True)),
                (
                    "contact",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT, to="main.contact"
                    ),
                ),
            ],
        ),
    ]
