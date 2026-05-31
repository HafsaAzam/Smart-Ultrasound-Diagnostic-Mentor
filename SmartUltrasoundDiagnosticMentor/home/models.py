from django.db import models
from django.utils import timezone
from accounts.models import DoctorProfile
from django.contrib.auth.models import User
from django.conf import settings
from django.utils.timezone import localtime
from django.core.validators import MinValueValidator, RegexValidator

# -----------------------
# Appointment
# -----------------------


class UltrasoundImage(models.Model):
    patient = models.ForeignKey(User, on_delete=models.CASCADE)
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, null=True)
    image = models.ImageField(upload_to='ultrasound/')
    image_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Image {self.id} - {self.patient.username}"
    
class DiagnosticReport(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ForeignKey(UltrasoundImage, on_delete=models.CASCADE)

    # ADD THIS HERE
    user_report_number = models.IntegerField(default=0)
    report_code = models.CharField(max_length=20, unique=True, null=True, blank=True)    
    patient_name = models.CharField(max_length=150, null=True, blank=True)

    age = models.IntegerField(validators=[MinValueValidator(0)])
    gender = models.CharField(max_length=10)
    weight = models.FloatField(validators=[MinValueValidator(0.0)])

    prediction = models.CharField(max_length=100, default="Unknown")
    nodule_status = models.CharField(max_length=100, default="Unknown")
    summary = models.TextField(default="No summary")

    report_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.patient_name or self.user.username} - Report {self.report_code or self.id}"
    

class ScanHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ForeignKey(UltrasoundImage, on_delete=models.CASCADE)
    report = models.ForeignKey('DiagnosticReport', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    # NEW FIELD
    user_scan_number = models.IntegerField(default=1)

class DoctorReview(models.Model):
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name="reviews")
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    rating = models.IntegerField(validators=[MinValueValidator(1)])  # 1–5
    comment = models.TextField(validators=[RegexValidator(regex=r'^\s*$', inverse_match=True, message='Comment cannot be empty or just spaces.')])

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.doctor.user.get_full_name()} - {self.rating}"
    
class Bookmark(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'doctor')

class RecordBookmark(models.Model):
    RECORD_TYPES = [
        ('appointment', 'Appointment'),
        ('report', 'Report'),
        ('image', 'Ultrasound Image'),
        ('scan', 'Scan History'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='record_bookmarks')
    record_type = models.CharField(max_length=20, choices=RECORD_TYPES)
    record_id = models.IntegerField()
    label = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'record_type', 'record_id')

    def __str__(self):
        return f"{self.user.username} bookmarked {self.record_type} #{self.record_id}"



class ContactMessage(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200, blank=True)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.first_name} {self.last_name}"

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username}"