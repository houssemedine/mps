# Generated by Django 4.0.5 on 2022-11-21 14:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0021_remove_shopfloor_shared_shopfloor_product'),
    ]

    operations = [
        migrations.CreateModel(
            name='Planning',
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
                ('name', models.CharField(max_length=200)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]