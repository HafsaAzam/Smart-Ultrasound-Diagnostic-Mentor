from django.db import models
from django.contrib.auth.models import User
from accounts.models import DoctorProfile
from django.utils import timezone
import datetime

class Appointment(models.Model):
    patient = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    patient_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15, blank=True, null=True)
    doctor = models.ForeignKey(
        DoctorProfile, on_delete=models.CASCADE, limit_choices_to={'is_verified': True}
    )
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    status = models.CharField(
        max_length=10,
        choices=[('pending','Pending'), ('accepted','Accepted'), ('rejected','Rejected')],
        default='pending'
    )

    @property
    def is_done(self):
        """Returns True if this accepted appointment's date+time is in the past."""
        if self.status != 'accepted':
            return False
        now = timezone.localtime(timezone.now())
        appt_dt = datetime.datetime.combine(self.appointment_date, self.appointment_time)
        appt_dt = timezone.make_aware(appt_dt, now.tzinfo)
        return now > appt_dt

    @property
    def is_missed(self):
        """Returns True if this pending appointment's date+time is in the past."""
        if self.status != 'pending':
            return False
        now = timezone.localtime(timezone.now())
        appt_dt = datetime.datetime.combine(self.appointment_date, self.appointment_time)
        appt_dt = timezone.make_aware(appt_dt, now.tzinfo)
        return now > appt_dt

    def __str__(self):
        return f"{self.patient_name} - {self.doctor}"