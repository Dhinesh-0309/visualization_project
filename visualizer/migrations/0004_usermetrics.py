# Generated by Django 5.1.3 on 2024-11-16 18:08

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('visualizer', '0003_rename_csv_file_csvupload_file'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserMetrics',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('total_sales', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('total_purchases', models.IntegerField(default=0)),
                ('top_product', models.CharField(blank=True, max_length=255, null=True)),
                ('top_location', models.CharField(blank=True, max_length=255, null=True)),
                ('highest_sales_month', models.IntegerField(default=0)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]