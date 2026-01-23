import magic
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.template.defaultfilters import filesizeformat

from django.utils.deconstruct import deconstructible

@deconstructible
class FileValidator:
    """
    文件验证器
    
    用于验证上传文件是否符合要求，包括：
    1. 文件大小限制 (max_size)
    2. 文件扩展名限制 (allowed_extensions)
    3. 文件 MIME 类型限制 (allowed_mimetypes) - 基于文件内容 (Magic Numbers) 检查，防止伪造扩展名
    """

    def __init__(self, max_size=None, allowed_extensions=None, allowed_mimetypes=None):
        self.max_size = max_size
        self.allowed_extensions = allowed_extensions
        self.allowed_mimetypes = allowed_mimetypes

    def __call__(self, value):
        try:
            # 检查文件大小 (Check file size)
            if self.max_size is not None and value.size > self.max_size:
                raise ValidationError(
                    _('文件大小不能超过 %(size)s。当前大小为 %(current_size)s。') % {
                        'size': filesizeformat(self.max_size),
                        'current_size': filesizeformat(value.size)
                    }
                )
        except FileNotFoundError:
            # 如果文件不存在（可能是旧数据的残留引用），跳过验证
            return

        # 检查文件扩展名 (Check extension)
        if self.allowed_extensions:
            ext = value.name.split('.')[-1].lower()
            if ext not in self.allowed_extensions:
                raise ValidationError(
                    _('不支持的文件扩展名 "%(ext)s"。允许的扩展名: %(allowed_extensions)s。') % {
                        'ext': ext,
                        'allowed_extensions': ', '.join(self.allowed_extensions)
                    }
                )

        # 检查文件内容类型 (Check content type using magic numbers)
        if self.allowed_mimetypes:
            try:
                # 读取前 2048 字节进行 magic 检查，然后重置指针
                initial_pos = value.tell()
                value.seek(0)
                try:
                    mime = magic.from_buffer(value.read(2048), mime=True)
                finally:
                    value.seek(initial_pos)

                if mime not in self.allowed_mimetypes:
                    raise ValidationError(
                        _('不支持的文件类型 "%(mime)s"。允许的类型: %(allowed_mimetypes)s。') % {
                            'mime': mime,
                            'allowed_mimetypes': ', '.join(self.allowed_mimetypes)
                        }
                    )
            except FileNotFoundError:
                # 同样捕获读取时的文件不存在错误
                return

# 预定义验证器 (Pre-defined validators)
validate_image_file = FileValidator(
    max_size=5 * 1024 * 1024,  # 限制为 5MB
    allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'webp'],
    allowed_mimetypes=['image/jpeg', 'image/png', 'image/gif', 'image/webp']
)
