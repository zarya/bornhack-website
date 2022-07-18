# Generated by Django 3.2.14 on 2022-07-18 10:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0078_remove_order_refunded'),
    ]

    operations = [
        migrations.AddField(
            model_name='creditnote',
            name='refund',
            field=models.OneToOneField(blank=True, help_text='The Refund this CreditNote relates to, if any.', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='refunds', to='shop.refund'),
        ),
    ]
