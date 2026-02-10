from django.core.management.base import BaseCommand
from django.conf import settings
from core.models import Media
import os
import mimetypes


class Command(BaseCommand):
    help = "Scan media directory and register files in Media library"

    def handle(self, *args, **options):
        media_root = settings.MEDIA_ROOT
        os.path.join(media_root, "uploads")

        # Ensure uploads dir exists (this is where new uploads go)
        # But we also want to scan legacy 'posts/' and 'friend_links/' etc.

        count = 0
        skipped = 0

        self.stdout.write(f"Scanning {media_root}...")

        for root, dirs, files in os.walk(media_root):
            for file in files:
                # Skip thumbnails or temp files
                if "cache" in root or "tmp" in root:
                    continue

                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, media_root)

                # Convert backslash to slash for DB consistency
                db_path = rel_path.replace("\\", "/")

                # Check if already exists
                if Media.objects.filter(file=db_path).exists():
                    skipped += 1
                    continue

                # Determine type
                mime_type, _ = mimetypes.guess_type(full_path)
                file_type = "other"
                if mime_type:
                    if mime_type.startswith("image"):
                        file_type = "image"
                    elif mime_type.startswith("video"):
                        file_type = "video"
                    elif mime_type.startswith("audio"):
                        file_type = "audio"
                    elif (
                        mime_type.startswith("text")
                        or "pdf" in mime_type
                        or "document" in mime_type
                    ):
                        file_type = "document"

                try:
                    size = os.path.getsize(full_path)

                    Media.objects.create(
                        file=db_path,
                        filename=file,
                        file_type=file_type,
                        file_size=size,
                        title=file,  # Default title
                    )
                    count += 1
                    if count % 100 == 0:
                        self.stdout.write(f"Processed {count} files...")
                except Exception as e:
                    self.stderr.write(
                        self.style.ERROR(f"Error processing {rel_path}: {e}")
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f"Done! Added {count} new files. Skipped {skipped} existing."
            )
        )
