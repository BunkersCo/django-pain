# Generated by Django 2.1 on 2018-08-15 04:42

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('django_pain', '0012_invoice'),
    ]

    operations = [
        migrations.CreateModel(
            name='Client',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('handle', models.TextField(verbose_name='Client ID')),
                ('remote_id', models.IntegerField()),
                ('payment', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='client', to='django_pain.BankPayment')),
            ],
        ),
    ]
