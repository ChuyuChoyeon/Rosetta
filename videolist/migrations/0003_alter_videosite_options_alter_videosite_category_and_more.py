# Generated by Django 5.2 on 2025-05-05 06:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('videolist', '0002_videosite_category'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='videosite',
            options={'ordering': ['-update_time'], 'verbose_name': '视频网站', 'verbose_name_plural': '视频网站'},
        ),
        migrations.AlterField(
            model_name='videosite',
            name='category',
            field=models.CharField(choices=[('movie', '影视'), ('anime', '动漫')], db_index=True, default='movie', max_length=10, verbose_name='分类'),
        ),
        migrations.AlterField(
            model_name='videosite',
            name='description',
            field=models.TextField(blank=True, verbose_name='网站描述'),
        ),
        migrations.AlterField(
            model_name='videosite',
            name='is_invalid',
            field=models.BooleanField(db_index=True, default=False, verbose_name='是否失效'),
        ),
        migrations.AlterField(
            model_name='videosite',
            name='name',
            field=models.CharField(db_index=True, max_length=200, verbose_name='网站名称'),
        ),
        migrations.AlterField(
            model_name='videosite',
            name='update_time',
            field=models.DateTimeField(auto_now=True, db_index=True, verbose_name='更新时间'),
        ),
        migrations.AddIndex(
            model_name='videosite',
            index=models.Index(fields=['category', 'is_invalid'], name='videolist_v_categor_5a0f4f_idx'),
        ),
    ]
