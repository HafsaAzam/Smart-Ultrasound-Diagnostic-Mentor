from django import forms
from appointment.models import Appointment
from home.models import UltrasoundImage

class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['doctor', 'appointment_date', 'appointment_time']  # must match model
        widgets = {
            'appointment_date': forms.DateInput(attrs={'type':'date'}),
            'appointment_time': forms.TimeInput(attrs={'type':'time'}),
        }

class UltrasoundImageForm(forms.ModelForm):
    class Meta:
        model = UltrasoundImage
        fields = ['image']