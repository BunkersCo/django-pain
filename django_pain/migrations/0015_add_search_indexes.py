# Generated by Django 2.1 on 2018-10-22 05:59

from django.db import migrations, models

import django_pain.constants


class Migration(migrations.Migration):

    dependencies = [
        ('django_pain', '0014_remove_bankpayment_objective'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bankpayment',
            name='create_time',
            field=models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Create time'),
        ),
        migrations.AlterField(
            model_name='bankpayment',
            name='state',
            field=models.TextField(choices=[(django_pain.constants.PaymentState('imported'), 'imported'), (django_pain.constants.PaymentState('processed'), 'processed'), (django_pain.constants.PaymentState('deferred'), 'not identified'), (django_pain.constants.PaymentState('exported'), 'exported')], db_index=True, default=django_pain.constants.PaymentState('imported'), verbose_name='Payment state'),
        ),
        migrations.AlterField(
            model_name='bankpayment',
            name='transaction_date',
            field=models.DateField(db_index=True, verbose_name='Transaction date'),
        ),
    ]
