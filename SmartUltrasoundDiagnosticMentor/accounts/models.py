from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator

class UserProfile(models.Model):
    ROLE_CHOICES = (
        ('patient', 'Patient'),
        ('doctor', 'Doctor'),
    )
    user = models.OneToOneField(
        User, on_delete=models.CASCADE) 
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='patient'
    )

    def __str__(self):
        return self.user.username


class DoctorProfile(models.Model):
    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='doctor_profile'
    )

    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    age = models.PositiveIntegerField(validators=[MinValueValidator(0)])
    weight = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0.0)])
    height = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0.0)])
    experience = models.PositiveIntegerField()

    # ✅ NEW FIELDS
    phone = models.CharField(max_length=15, blank=True, null=True)
    office_location = models.CharField(max_length=255, blank=True, null=True)
    degrees = models.CharField(max_length=255, default="N/A")
    # ✅ Separate images
    profile_photo = models.ImageField(upload_to="doctor_photos/", blank=True, null=True)  # doctor image
    degree_document = models.ImageField(upload_to="degree_docs/", null=True, blank=True)  # proof (nullable in DB, required in form)

    # ✅ Verification
    is_verified = models.BooleanField(default=False)
    is_rejected = models.BooleanField(default=False)

    # ✅ Rating system
    average_rating = models.FloatField(default=0)
    total_reviews = models.PositiveIntegerField(default=0)
    # ✅ Availability
    is_available = models.BooleanField(default=True)
    def __str__(self):
        return f"{self.user.get_full_name()}"
    
    
class PatientProfile(models.Model):
    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='patient_profile'
    )
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    age = models.PositiveIntegerField(validators=[MinValueValidator(0)], default=30)
    weight = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0.0)])
    height = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0.0)])
    profile_photo = models.ImageField(upload_to="patient_photos/", blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return self.user.username
    
class doctor_degree(models.Model):
    image = models.ImageField(upload_to="profiles/")

    @property
    def bmi_category(self):
        # This model doesn't have bmi or weight/height. 
        # Assuming it was meant to be on PatientProfile or just placeholder.
        # Returning "Unknown" to prevent crash.
        return "Unknown"

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail

@receiver(post_save, sender=DoctorProfile)
def notify_doctor_status(sender, instance, created, **kwargs):
    from home.models import Notification
    if not created:
        # Here we just blindly notify if it's rejected. In a robust app we'd track state changes.
        if instance.is_rejected:
            subject = 'Update on Your Doctor Account - Smart Ultrasound Diagnostic Mentor'
            message = f'Hi {instance.user.first_name},\n\nWe regret to inform you that your doctor account has been rejected by the admin. However, you can still continue to use our platform as a patient.\n\nThank you.'
            from_email = settings.EMAIL_HOST_USER
            recipient_list = [instance.user.email]
            
            try:
                send_mail(subject, message, from_email, recipient_list)
            except Exception as e:
                print(f"Error sending email: {e}")
                
            Notification.objects.get_or_create(
                user=instance.user, 
                message="Your doctor account application was rejected. You can continue using the platform as a patient."
            )
        elif instance.is_verified:
            Notification.objects.get_or_create(
                user=instance.user, 
                message="Your doctor account has been verified and activated!"
            )