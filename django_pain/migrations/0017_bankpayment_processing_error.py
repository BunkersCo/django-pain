# Generated by Django 2.1.5 on 2019-02-19 02:34

from django.db import migrations, models
import django_pain.constants


class Migration(migrations.Migration):

    dependencies = [
        ('django_pain', '0016_unique_account_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='bankpayment',
            name='processing_error',
            field=models.TextField(blank=True, choices=[(django_pain.constants.PaymentProcessingError('duplicity'), 'Duplicate payment'), (django_pain.constants.PaymentProcessingError('insufficient_amount'), 'Received amount is lower than expected'), (django_pain.constants.PaymentProcessingError('excessive_amount'), 'Received amount is greater than expected'), (django_pain.constants.PaymentProcessingError('overdue'), 'Payment is overdue'), (django_pain.constants.PaymentProcessingError('manually_broken'), 'Payment was manually broken')], null=True, verbose_name='Processing error'),
        ),
    ]
