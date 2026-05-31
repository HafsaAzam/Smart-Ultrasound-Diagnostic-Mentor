from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import HealthProfile, LifestyleRecommendation

@admin.register(HealthProfile)
class HealthProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "age", "gender", "weight", "height", "activity_level", "smoking_status_vibe")
    list_filter = ("gender", "activity_level", "smoking_status")
    search_fields = ("user__username", "user__email")
    
    def smoking_status_vibe(self, obj):
        if not obj.smoking_status:
            # Green cross in circle
            return mark_safe(
                '<span style="display:inline-block; width:24px; height:24px; background:green; color:white; border-radius:50%; text-align:center; line-height:24px;"><i class="fas fa-times"></i></span>'
            )
        # Red cross in circle
        return mark_safe(
            '<span style="display:inline-block; width:24px; height:24px; background:red; color:white; border-radius:50%; text-align:center; line-height:24px;"><i class="fas fa-times"></i></span>'
        )
    smoking_status_vibe.short_description = "Smoking Status"

    fieldsets = (
        ('Core Info', {
            'fields': ('user', 'age', 'gender', 'weight', 'height')
        }),
        ('Habits', {
            'fields': ('activity_level', 'dietary_preference', 'smoking_status', 'alcohol_consumption', 'hours_of_sleep')
        }),
        ('Meals & Routine', {
            'fields': ('breakfast', 'lunch', 'dinner', 'other_routine')
        }),
        ('Medical Context', {
            'fields': ('health_conditions', 'allergies')
        }),
    )

@admin.register(LifestyleRecommendation)
class LifestyleRecommendationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'bmi', 'bmi_category', 'date')
    list_filter = ('bmi_category', 'date')
    search_fields = ('user__username', 'bmi_category')
    readonly_fields = ('date',)
