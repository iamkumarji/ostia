"""Register the JPEGs in media/original_images as Wagtail images.

Run before seed_site so the seeder can attach photographs by title:

    python manage.py import_photos
"""
from pathlib import Path

from django.conf import settings
from django.core.files.images import ImageFile
from django.core.management.base import BaseCommand
from wagtail.images.models import Image


class Command(BaseCommand):
    help = "Import media/original_images/*.jpg into the Wagtail image library."

    def handle(self, *args, **options):
        source = Path(settings.MEDIA_ROOT) / "original_images"
        if not source.exists():
            self.stdout.write(self.style.WARNING(f"No such directory: {source}"))
            return

        created = 0
        for path in sorted(source.glob("*.jpg")):
            title = path.stem
            if Image.objects.filter(title=title).exists():
                continue
            with path.open("rb") as handle:
                image = Image(title=title, file=ImageFile(handle, name=path.name))
                image.save()
            created += 1

        self.stdout.write(
            self.style.SUCCESS(f"Imported {created} image(s); library now holds {Image.objects.count()}.")
        )
