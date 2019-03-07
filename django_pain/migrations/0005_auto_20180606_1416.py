# Generated by Django 2.0.4 on 2018-06-06 14:16

from django.db import migrations, models

import django_pain.constants


class Migration(migrations.Migration):

    dependencies = [
        ('django_pain', '0004_auto_20180605_1228'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bankpayment',
            name='state',
            field=models.TextField(choices=[(django_pain.constants.PaymentState('imported'), 'imported'), (django_pain.constants.PaymentState('processed'), 'processed'), (django_pain.constants.PaymentState('deferred'), 'deferred'), (django_pain.constants.PaymentState('exported'), 'exported')], default=django_pain.constants.PaymentState('imported'), verbose_name='Payment state'),
        ),
    ]
