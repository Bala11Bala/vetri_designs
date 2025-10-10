from django.db import models
from django.contrib.auth.models import User

class Project(models.Model):
    VISIBILITY_CHOICES = [
        ("Public", "Public"),
        ("Private", "Private"),
    ]

    LICENSE_CHOICES = [
        ("All Rights Reserved", "All Rights Reserved"),
        ("Creative Commons", "Creative Commons"),
        ("MIT", "MIT"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    tags = models.CharField(max_length=255, blank=True)  # comma-separated
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default="Public")
    license = models.CharField(max_length=50, choices=LICENSE_CHOICES, default="All Rights Reserved")
    allow_downloads = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    views = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.title} by {self.user.username}"


class ProjectImage(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="projects/")

    def __str__(self):
        return f"Image for {self.project.title}"



from django.contrib.auth.models import User
from django.db import models

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    course = models.CharField(max_length=100, blank=True)
    mobile = models.CharField(max_length=15, blank=True)
    location = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)
    profile_image = models.ImageField(upload_to="profiles/", default="profiles/default.jpg")
    appreciation_count = models.PositiveIntegerField(default=0) 

    def __str__(self):
        return self.user.username



class HiringInquiry(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="inquiries")
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_inquiries")
    hiring_for = models.CharField(max_length=255)
    categories = models.CharField(max_length=255)
    budget = models.CharField(max_length=100)
    description = models.TextField()
    note = models.TextField(blank=True, null=True)
    hiring_type = models.CharField(
        max_length=50, choices=[("Freelancing", "Freelancing"), ("Company", "Company")]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Inquiry by {self.sender.username} for {self.project.title}"



class Message(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_messages")
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received_messages")
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    def __str__(self):
        return f"Message from {self.sender.username} to {self.recipient.username} for {self.project.title}"





# from django.db.models.signals import post_save
# from django.dispatch import receiver

# @receiver(post_save, sender=Project)
# def create_message_on_project_upload(sender, instance, created, **kwargs):
#     if created:
#         # Get the admin user (assuming only one superuser)
#         admin_user = User.objects.filter(is_superuser=True).first()
#         if admin_user:
#             Message.objects.create(
#                 project=instance,
#                 sender=admin_user,
#                 recipient=instance.user,
#                 content=f"Your project '{instance.title}' has been successfully uploaded. Admin will review it shortly."
#             )

from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=Project)
def notify_admin_on_project_upload(sender, instance, created, **kwargs):
    if created:
        # Only notify admin
        admin_user = User.objects.filter(is_superuser=True).first()
        if admin_user:
            Message.objects.create(
                project=instance,
                sender=instance.user,       # Student is sender
                recipient=admin_user,       # Admin is recipient
                content=f"{instance.user.username} uploaded project '{instance.title}'."
            )



class Like(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='liked_projects')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('project', 'user')  # Prevent multiple likes by same user

    def __str__(self):
        return f"{self.user.username} liked {self.project.title}"
