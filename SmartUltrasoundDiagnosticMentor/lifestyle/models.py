from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator

class HealthProfile(models.Model):
    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    )
    ACTIVITY_CHOICES = (
        ('sedentary', 'Sedentary (little or no exercise)'),
        ('light', 'Light (exercise 1-3 days/week)'),
        ('moderate', 'Moderate (exercise 3-5 days/week)'),
        ('active', 'Active (exercise 6-7 days/week)'),
        ('very_active', 'Very Active (hard exercise & physical job)'),
    )
    DIET_CHOICES = (
        ('no_preference', 'No Preference'),
        ('vegetarian', 'Vegetarian'),
        ('vegan', 'Vegan'),
        ('halal', 'Halal'),
        ('keto', 'Keto'),
        ('paleo', 'Paleo'),
    )
    ALCOHOL_CHOICES = (
        ('never', 'Never'),
        ('occasionally', 'Occasionally'),
        ('regularly', 'Regularly'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='health_profile_new')
    age = models.PositiveIntegerField(validators=[MinValueValidator(0)], default=30)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='male')
    weight = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0.0)], help_text="Weight in kg")
    height = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0.0)], help_text="Height in cm")
    activity_level = models.CharField(max_length=20, choices=ACTIVITY_CHOICES, default='sedentary')
    health_conditions = models.TextField(blank=True, null=True, help_text="List conditions, e.g., Diabetes, Hypertension")
    allergies = models.TextField(blank=True, null=True, help_text="List any allergies")
    dietary_preference = models.CharField(max_length=20, choices=DIET_CHOICES, default='no_preference')
    smoking_status = models.BooleanField(default=False)
    alcohol_consumption = models.CharField(max_length=20, choices=ALCOHOL_CHOICES, default='never')

    # New fields for detailed assessment
    hours_of_sleep = models.PositiveIntegerField(null=True, blank=True, help_text="Average hours of sleep per night")
    breakfast = models.TextField(blank=True, null=True, help_text="Typical breakfast details")
    lunch = models.TextField(blank=True, null=True, help_text="Typical lunch details")
    dinner = models.TextField(blank=True, null=True, help_text="Typical dinner details")
    other_routine = models.TextField(blank=True, null=True, help_text="Any other important daily routines")

    def __str__(self):
        return f"Health Profile - {self.user.username}"

class LifestyleRecommendation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lifestyle_recommendations_new')

    # Health metrics at the time of recommendation
    bmi = models.FloatField(null=True, blank=True)
    bmi_category = models.CharField(max_length=50, null=True, blank=True)

    # Detailed advice pillars
    nutrition_advice = models.TextField()
    activity_advice = models.TextField()
    sleep_advice = models.TextField()
    mental_health_advice = models.TextField()
    safety_alerts = models.TextField(blank=True, null=True)

    # Explainability
    reasoning = models.TextField()
    
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Recommendation for {self.user.username} ({self.date.date()})"
