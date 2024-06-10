# Generated by Django 5.0.6 on 2024-06-10 21:51

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0010_domain_owner"),
    ]

    operations = [
        migrations.AddField(
            model_name="contact",
            name="owner",
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.PROTECT,
                to=settings.AUTH_USER_MODEL,
            ),
            preserve_default=False,
        ),
    ]