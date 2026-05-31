from django import forms
from .models import HealthProfile

class HealthProfileForm(forms.ModelForm):
    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    )

    age = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter your age'}),
        label="Age",
        required=False
    )
    gender = forms.ChoiceField(
        choices=GENDER_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Gender",
        required=False
    )
    weight = forms.FloatField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'placeholder': 'Weight in kg'}),
        label="Weight (kg)",
        required=False
    )
    height = forms.FloatField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'placeholder': 'Height in cm'}),
        label="Height (cm)",
        required=False
    )

    smoking_status = forms.TypedChoiceField(
        choices=[(True, 'Yes'), (False, 'No')],
        coerce=lambda x: str(x).lower() == 'true',
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label="Do you smoke?"
    )

    class Meta:
        model = HealthProfile
        fields = [
            'age', 'gender', 'weight', 'height',
            'activity_level', 'health_conditions', 'allergies', 
            'dietary_preference', 'smoking_status', 'alcohol_consumption',
            'hours_of_sleep', 'breakfast', 'lunch', 'dinner', 'other_routine'
        ]
        widgets = {
            'activity_level': forms.Select(attrs={'class': 'form-control'}),
            'health_conditions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'e.g. Diabetes, Hypertension, etc.'}),
            'allergies': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'e.g. Peanuts, Pollen (Leave empty if none)'}),
            'dietary_preference': forms.Select(attrs={'class': 'form-control'}),
            'alcohol_consumption': forms.Select(attrs={'class': 'form-control'}),
            'hours_of_sleep': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Average hours per night'}),
            'breakfast': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'What do you eat for breakfast?'}),
            'lunch': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'What do you eat for lunch?'}),
            'dinner': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'What do you eat for dinner?'}),
            'other_routine': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Other habits (e.g. tea, snacking, work schedule)'}),
        }
        labels = {
            'health_conditions': 'Existing Health Conditions / Diseases',
            'activity_level': 'Typical Activity Level',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['smoking_status'].widget.attrs.update({'class': 'form-check-input'})
