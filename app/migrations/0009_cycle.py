# Generated by Django 4.0.5 on 2022-07-01 07:20

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0008_product_profit_center'),
    ]

    operations = [
        migrations.CreateModel(
            name='Cycle',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('created_by', models.CharField(default='Marwa', max_length=30)),
                ('updated_by', models.CharField(default='Marwa', max_length=30)),
                ('is_deleted', models.BooleanField(default=False)),
                ('deleted_by', models.CharField(max_length=30, null=True)),
                ('deleted_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('restored_at', models.DateTimeField(auto_now=True, null=True)),
                ('restored_by', models.CharField(default='Marwa', max_length=30, null=True)),
                ('profit_center', models.CharField(max_length=200)),
                ('date', models.DateField()),
                ('smooth_family', models.CharField(max_length=100)),
                ('division', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.division')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
