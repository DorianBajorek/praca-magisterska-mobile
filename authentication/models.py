from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import RegexValidator
# Create your models here.

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    registration_date = models.DateTimeField(default=timezone.now)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    phone_number  = models.TextField(max_length=15, default = "", validators=[
            RegexValidator(
                regex=r'^\d{9}$',  # Example regex for international phone numbers
                message="Phone number must be entered in the format: '+999999999'. Up to 9 digits allowed."
            )
        ])
    is_email_verified = models.BooleanField(default=False)
    is_social_register = models.BooleanField(default=False)
    
    def __str__(self):
        return self.user.username