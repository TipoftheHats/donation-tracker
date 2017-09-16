# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import tracker.validators


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0038_merge'),
    ]

    operations = [
        migrations.AlterField(
            model_name='donationbid',
            name='amount',
            field=models.DecimalField(default=0, max_digits=20, decimal_places=2, validators=[tracker.validators.positive, tracker.validators.nonzero]),
        ),
    ]
