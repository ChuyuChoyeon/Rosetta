from django.db import migrations, models
from django.db.models import F


def fill_published_at(apps, schema_editor):
    Post = apps.get_model("blog", "Post")
    Post.objects.filter(status="published", published_at__isnull=True).update(
        published_at=F("created_at")
    )


class Migration(migrations.Migration):
    dependencies = [
        ("blog", "0002_delete_subscriber_remove_post_notification_sent"),
    ]

    operations = [
        migrations.AddField(
            model_name="post",
            name="published_at",
            field=models.DateTimeField(
                blank=True, db_index=True, null=True, verbose_name="发布时间"
            ),
        ),
        migrations.AddIndex(
            model_name="post",
            index=models.Index(fields=["status", "published_at"], name="blog_post_status_published_at_idx"),
        ),
        migrations.RunPython(fill_published_at, reverse_code=migrations.RunPython.noop),
    ]
