from django import forms
from .models import Appointment
from django.core.exceptions import ValidationError
from datetime import date as make_date, time as make_time

class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['phone', 'doctor', 'appointment_date', 'appointment_time']
        widgets = {
            'appointment_date': forms.DateInput(attrs={'type': 'date'}),
            'appointment_time': forms.TimeInput(attrs={'type': 'time'}),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(AppointmentForm, self).__init__(*args, **kwargs)

        # If the logged-in user is a doctor, exclude them from the doctor dropdown
        if self.request and self.request.user and self.request.user.is_authenticated:
            try:
                from accounts.models import DoctorProfile
                doctor_profile = DoctorProfile.objects.get(user=self.request.user)
                self.fields['doctor'].queryset = self.fields['doctor'].queryset.exclude(id=doctor_profile.id)
            except DoctorProfile.DoesNotExist:
                pass

    def clean(self):
        cleaned_data = super().clean()
        doctor = cleaned_data.get('doctor')
        date = cleaned_data.get('appointment_date')
        time = cleaned_data.get('appointment_time')

        if doctor and date and time:
            from django.utils import timezone
        today = make_date.today()

        # Past date not allowed
        if date < today:
            raise ValidationError("You cannot book an appointment for past dates.")

        # Allow today but only future time
        if date == today:
            now = timezone.localtime().time()
            if time <= now:
                raise ValidationError("Please select a future time for today.")

        # Time limits
        if time < make_time(10, 0):
            raise ValidationError("Appointments start from 10:00 AM.")

        if time > make_time(17, 30):
            raise ValidationError("Last appointment time is 5:30 PM.")

        # Self booking
        if self.request and self.request.user.is_authenticated:
            if doctor.user == self.request.user:
                raise ValidationError("You cannot book an appointment with yourself.")

        # Doctor slot already booked
        exists = Appointment.objects.filter(
            doctor=doctor,
            appointment_date=date,
            appointment_time=time
        ).exists()

        if exists:
            raise ValidationError(f"This time slot ({time}) is already booked. Please choose another time.")

        # Same user double booking
        if self.request and self.request.user.is_authenticated:
            exists_user = Appointment.objects.filter(
                patient=self.request.user,
                appointment_date=date,
                appointment_time=time
            ).exists()

            if exists_user:
                raise ValidationError("You already have an appointment at this time.")

        return cleaned_data