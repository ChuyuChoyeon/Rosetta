import magic
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.template.defaultfilters import filesizeformat

from django.utils.deconstruct import deconstructible

@deconstructible
class FileValidator:
    """
    Validator for files, checking content_type, file content (magic numbers) and size.
    """

    def __init__(self, max_size=None, allowed_extensions=None, allowed_mimetypes=None):
        self.max_size = max_size
        self.allowed_extensions = allowed_extensions
        self.allowed_mimetypes = allowed_mimetypes

    def __call__(self, value):
        # Check file size
        if self.max_size is not None and value.size > self.max_size:
            raise ValidationError(
                _('File size must be no more than %(size)s. Current size is %(current_size)s.') % {
                    'size': filesizeformat(self.max_size),
                    'current_size': filesizeformat(value.size)
                }
            )

        # Check extension
        if self.allowed_extensions:
            ext = value.name.split('.')[-1].lower()
            if ext not in self.allowed_extensions:
                raise ValidationError(
                    _('File extension "%(ext)s" is not allowed. Allowed extensions are: %(allowed_extensions)s.') % {
                        'ext': ext,
                        'allowed_extensions': ', '.join(self.allowed_extensions)
                    }
                )

        # Check content type (magic numbers)
        if self.allowed_mimetypes:
            # Read first 2048 bytes for magic check
            initial_pos = value.tell()
            value.seek(0)
            try:
                mime = magic.from_buffer(value.read(2048), mime=True)
            finally:
                value.seek(initial_pos)

            if mime not in self.allowed_mimetypes:
                raise ValidationError(
                    _('File type "%(mime)s" is not allowed. Allowed types are: %(allowed_mimetypes)s.') % {
                        'mime': mime,
                        'allowed_mimetypes': ', '.join(self.allowed_mimetypes)
                    }
                )

# Pre-defined validators
validate_image_file = FileValidator(
    max_size=5 * 1024 * 1024,  # 5MB
    allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'webp'],
    allowed_mimetypes=['image/jpeg', 'image/png', 'image/gif', 'image/webp']
)
