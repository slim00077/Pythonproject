from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.utils import timezone
from django.utils.deconstruct import deconstructible

ALLOWED_IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'webp']


@deconstructible
class MaxFileSizeValidator:
    def __init__(self, max_mb=None):
        self.max_mb = max_mb

    def __call__(self, file):
        limit_mb = self.max_mb or settings.ECOTEAMS_MAX_UPLOAD_MB
        if file and file.size > limit_mb * 1024 * 1024:
            raise ValidationError(
                f'Le fichier est trop volumineux (maximum {limit_mb} Mo).',
                code='file_too_large',
            )

    def __eq__(self, other):
        return isinstance(other, MaxFileSizeValidator) and self.max_mb == other.max_mb


@deconstructible
class UploadToUUID:
    """Stores uploads under ``<prefix>/<year>/<month>/<random>.<ext>``.

    Random names avoid collisions and never reuse a client-supplied path.
    """

    def __init__(self, prefix):
        self.prefix = prefix

    def __call__(self, instance, filename):
        extension = Path(filename).suffix.lower()
        return f'{self.prefix}/{timezone.now():%Y/%m}/{uuid4().hex}{extension}'

    def __eq__(self, other):
        return isinstance(other, UploadToUUID) and self.prefix == other.prefix


image_validators = [
    FileExtensionValidator(allowed_extensions=ALLOWED_IMAGE_EXTENSIONS),
    MaxFileSizeValidator(),
]


ALLOWED_IMAGE_FORMATS = {'JPEG', 'PNG', 'WEBP'}


def check_image_format(upload):
    """Reject a file whose real content (read by Pillow) is not JPEG, PNG or WebP, whatever its extension says.

    ``forms.ImageField`` has already verified the file and exposes the parsed image as ``upload.image``;
    stored files (no ``image`` attribute) are left alone.
    """
    image = getattr(upload, 'image', None)
    if image is not None and image.format not in ALLOWED_IMAGE_FORMATS:
        raise ValidationError('Format d’image non pris en charge : utilisez une image JPEG, PNG ou WebP.',
                              code='bad_image_format')
    return upload
