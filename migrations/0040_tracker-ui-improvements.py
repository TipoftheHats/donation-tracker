# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0039_auto_20170916_1329'),
    ]

    operations = [
        migrations.AddField(
            model_name='donation',
            name='prioritystate',
            field=models.BooleanField(default=False),
        ),
    ]
