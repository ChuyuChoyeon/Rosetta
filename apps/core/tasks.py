import time
from celery import shared_task
from django.core.cache import cache
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def debug_task(self):
    """
    一个简单的调试任务，打印请求信息。
    用于验证 Celery 是否正常工作。
    """
    print(f"Request: {self.request!r}")
    return f"Debug task executed at {timezone.now()}"


@shared_task
def send_test_email(recipient_list, subject="Test Email from Rosetta"):
    """
    向指定收件人发送测试邮件。

    Args:
        recipient_list (list): 电子邮件地址列表。
        subject (str): 邮件主题。
    """
    logger.info(f"Sending email to {recipient_list}")
    try:
        # 验证 recipient_list 是否为列表
        if not isinstance(recipient_list, (list, tuple)):
            recipient_list = [recipient_list]

        send_mail(
            subject,
            f"This is a test email sent from Rosetta at {timezone.now()}.",
            settings.DEFAULT_FROM_EMAIL,
            recipient_list,
            fail_silently=False,
        )
        return f"Email sent to {len(recipient_list)} recipients"
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        # 在生产环境中，可能需要重试机制
        # raise self.retry(exc=e, countdown=60)
        raise


@shared_task
def backup_database_task():
    """
    后台执行数据库备份任务。
    自动检测数据库类型：
    - SQLite: 执行文件级二进制备份 (更完整，恢复更快)
    - 其他: 执行 dumpdata (JSON 格式)
    """
    try:
        from core.utils import create_backup

        filename = create_backup()
        return f"Backup created: {filename}"

    except Exception as e:
        logger.error(f"Database backup failed: {e}")
        raise


@shared_task
def clear_cache_task():
    """
    清除过期的缓存键。
    注意：大多数缓存后端会自动处理此问题，但这作为一个示例。
    """
    # 这只是一个虚拟示例，因为 Django 缓存后端通常会处理过期。
    # 如果需要，我们可以清除特定的模式。
    cache.clear()
    return "Cache cleared"


@shared_task(bind=True)
def long_running_process(self, seconds=10):
    """
    模拟一个带有进度更新的长时间运行进程。

    Args:
        seconds (int): 运行持续时间（秒）。
    """
    logger.info(f"Starting long process for {seconds} seconds")
    for i in range(seconds):
        time.sleep(1)
        # 更新进度（如果有跟踪机制，例如通过缓存或数据库）
        # self.update_state(state='PROGRESS', meta={'current': i, 'total': seconds})
        logger.info(f"Processing... {i + 1}/{seconds}")

    return "Process completed"
