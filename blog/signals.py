from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import Post, Subscriber


@receiver(post_save, sender=Post)
def send_notification_to_subscribers(sender, instance, created, **kwargs):
    """
    发送新文章通知给订阅者
    
    当文章发布 (status='published') 且尚未发送过通知时触发。
    """
    if instance.status == "published" and not instance.notification_sent:
        subscribers = Subscriber.objects.filter(is_active=True)
        if not subscribers.exists():
            return

        subject = f"【Rosetta Blog】新文章发布: {instance.title}"

        # 构建绝对 URL (Build absolute URL)
        protocol = getattr(settings, "META_SITE_PROTOCOL", "http")
        domain = getattr(settings, "META_SITE_DOMAIN", "localhost:8000")
        post_url = f"{protocol}://{domain}/post/{instance.slug}/"

        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@example.com")

        for s in subscribers:
            unsubscribe_url = f"{protocol}://{domain}/unsubscribe/{s.token}/"

            message = f"""
你好！

我们发布了一篇新文章：{instance.title}

{instance.excerpt}

点击阅读全文：
{post_url}

退订链接：
{unsubscribe_url}

感谢您的订阅！
Rosetta Blog Team
            """

            try:
                send_mail(
                    subject,
                    message,
                    from_email,
                    [s.email],
                    fail_silently=True,
                )
            except Exception as e:
                print(f"Failed to send email to {s.email}: {e}")

        # 标记为已发送 (Mark as sent)
        instance.notification_sent = True
        instance.save(update_fields=["notification_sent"])
