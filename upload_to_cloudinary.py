# upload_to_cloudinary.py

import os
import django
import cloudinary
import cloudinary.uploader
from django.conf import settings

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

# Load Cloudinary config from settings
cloudinary.config(
    cloud_name = settings.CLOUDINARY_STORAGE['CLOUD_NAME'],
    api_key = settings.CLOUDINARY_STORAGE['API_KEY'],
    api_secret = settings.CLOUDINARY_STORAGE['API_SECRET'],
    secure = True
)

from myapp.models import ProjectImage, Profile

# Upload project images
for pi in ProjectImage.objects.all():
    if pi.image and not str(pi.image).startswith('http'):
        print(f"Uploading {pi.image.name}...")
        result = cloudinary.uploader.upload(
            pi.image.path,
            folder="projects",
            public_id=os.path.splitext(os.path.basename(pi.image.name))[0],
            overwrite=True
        )
        pi.image = result['secure_url']
        pi.save()

# Upload profile images
for profile in Profile.objects.all():
    if profile.profile_image and not str(profile.profile_image).startswith('http'):
        print(f"Uploading {profile.profile_image.name}...")
        result = cloudinary.uploader.upload(
            profile.profile_image.path,
            folder="profiles",
            public_id=os.path.splitext(os.path.basename(profile.profile_image.name))[0],
            overwrite=True
        )
        profile.profile_image = result['secure_url']
        profile.save()

print("All existing images uploaded to Cloudinary!")
