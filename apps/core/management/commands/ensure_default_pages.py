from django.core.management.base import BaseCommand
from core.models import Page


class Command(BaseCommand):
    help = "Ensures default pages (like Privacy Policy) exist"

    def handle(self, *args, **options):
        self.stdout.write("Checking default pages...")

        # Privacy Policy Content
        privacy_content = """# 隐私政策

**生效日期：** 2024年01月01日

欢迎访问 {{ config.SITE_NAME }}（以下简称“本站”）。我们非常重视您的隐私保护。本隐私政策旨在向您说明我们如何收集、使用、存储和保护您的个人信息。

## 1. 我们收集的信息

当您访问本站或使用我们的服务时，我们可能会收集以下类型的信息：

*   **日志信息：** 包括您的 IP 地址、浏览器类型、访问时间、访问页面等服务器日志信息。
*   **交互信息：** 如果您发表评论或留言，我们会收集您提交的昵称、邮箱地址（仅用于通知，不会公开）和评论内容。
*   **Cookie：** 我们使用 Cookie 来改善用户体验，例如记住您的偏好设置。

## 2. 信息的使用

我们收集的信息主要用于：

*   提供和维护本站的服务。
*   改善网站内容和用户体验。
*   在您同意的情况下，向您发送相关通知（如评论回复）。
*   保障网站安全，防止欺诈和滥用。

## 3. 信息共享与披露

我们要么不共享您的个人信息，除非：

*   获得您的明确同意。
*   法律法规要求或响应政府部门的强制性命令。
*   为了保护本站或公众的权利、财产或安全。

## 4. 数据安全

我们采取合理的安全措施来保护您的个人信息，防止未经授权的访问、使用或泄露。

## 5. 您的权利

您有权查阅、更正或删除您的个人信息。如果您希望行使这些权利，请通过 {{ config.CONTACT_EMAIL }} 联系我们。

## 6. 变更通知

我们可能会不时更新本隐私政策。更新后的政策将发布在本页面，并更新“生效日期”。

## 7. 联系我们

如果您对本隐私政策有任何疑问，请联系：{{ config.SITE_EMAIL }}"""

        page, created = Page.objects.get_or_create(
            slug="privacy-policy",
            defaults={
                "title": "隐私政策",
                "content": privacy_content,
                "status": "published",
            },
        )

        if created:
            self.stdout.write(self.style.SUCCESS("Created 'Privacy Policy' page."))
        else:
            self.stdout.write("Privacy Policy page already exists.")
