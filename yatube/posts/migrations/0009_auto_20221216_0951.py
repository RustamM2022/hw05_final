# Generated by Django 2.2.16 on 2022-12-16 04:51

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0008_auto_20221216_0946'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='post',
            options={'ordering': ['-pub_date', 'id']},
        ),
    ]