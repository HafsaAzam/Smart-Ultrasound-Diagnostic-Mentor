from django.contrib import admin
from django.utils.html import format_html
from django.core.mail import send_mail
from django.conf import settings
from .models import DoctorProfile, PatientProfile, UserProfile
from home.models import DoctorReview

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role")
    list_filter = ("role",)
    search_fields = ("user__username", "user__email")

# accounts
class DoctorReviewInline(admin.TabularInline):
    model = DoctorReview
    extra = 0
    readonly_fields = ('patient', 'rating', 'comment', 'created_at')
    can_delete = False

@admin.register(DoctorProfile)
class DoctorAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "profile_photo_preview",
        "phone",
        "office_location",
        "gender",
        "age",
        "weight",
        "height",
        "degrees",
        "experience",
        "degree_doc_link",
        "is_verified",
        "average_rating",
        "approve_button",
        "reject_button",
    )
    inlines = [DoctorReviewInline]
    list_filter = ("is_verified", "gender")
    search_fields = ("user__username", "user__email", "phone", "office_location")

    def profile_photo_preview(self, obj):
        if obj.profile_photo:
            return format_html(
                '<img src="{0}" width="50" height="50" style="border-radius:50%; object-fit: cover;" />',
                obj.profile_photo.url
            )
        return "No Photo"
    profile_photo_preview.short_description = "Photo"

    def degree_doc_link(self, obj):
        if obj.degree_document:
            return format_html(
                '<a href="{0}" target="_blank" style="font-weight:bold; color:var(--accent);">View Degree</a>',
                obj.degree_document.url
            )
        return "No File"
    degree_doc_link.short_description = "Degree Doc"

    # Approve button
    def approve_button(self, obj):
        if not obj.is_verified:
            return format_html(
                '<a class="button" href="approve/{0}/" style="background:green;color:white;padding:8px 10px;">Approve</a>',
                obj.id
            )
        return "Approved"
    approve_button.short_description = "Approve"

    # Reject button
    def reject_button(self, obj):
        if not obj.is_rejected:
            return format_html(
                '<a class="button" href="reject/{0}/" style="background:red;color:white;padding:8px 10px;">Reject</a>',
                obj.id
            )
        return "Rejected"
    reject_button.short_description = "Reject"

    # Custom URLs
    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path("approve/<int:doctor_id>/", self.admin_site.admin_view(self.approve_doctor)),
            path("reject/<int:doctor_id>/", self.admin_site.admin_view(self.reject_doctor)),
        ]
        return custom_urls + urls

    # Approve logic
    def approve_doctor(self, request, doctor_id):
        doctor = DoctorProfile.objects.get(id=doctor_id)
        doctor.is_verified = True
        doctor.is_rejected = False
        doctor.user.is_active = True
        doctor.user.save()
        doctor.save()

        # Send email
        send_mail(
            "Doctor Account Approved",
            "Congratulations! Your doctor account has been approved on Smart Ultrasound Diagnostic Support.",
            settings.DEFAULT_FROM_EMAIL,
            [doctor.user.email],
            fail_silently=False,
        )

        self.message_user(request, "Doctor approved successfully.")
        from django.shortcuts import redirect
        return redirect("../")

    # Reject logic
    def reject_doctor(self, request, doctor_id):
        doctor = DoctorProfile.objects.get(id=doctor_id)
        doctor.is_rejected = True
        doctor.is_verified = False
        # IMPORTANT: Keep is_active=True so the user can still log in as a patient
        doctor.user.is_active = True
        doctor.user.save()
        doctor.save()

        # Send email
        try:
            send_mail(
                "Doctor Account Rejected",
                f"Hi {doctor.user.first_name},\n\nYour doctor account has been rejected on Smart Ultrasound Diagnostic Mentor. "
                f"However, you can still continue using the platform as a patient.\n\nThank you.",
                settings.DEFAULT_FROM_EMAIL,
                [doctor.user.email],
                fail_silently=True,
            )
        except Exception:
            pass

        self.message_user(request, f"Doctor '{doctor.user.get_full_name()}' rejected. They can still use the platform as a patient.")
        from django.shortcuts import redirect
        return redirect("../")

    fieldsets = (
        (None, {
            'fields': (
                'user',
                'profile_photo',
                'phone',
                'office_location',
                'gender',
                'degrees',
                'experience',
                'degree_document',
                'is_verified',
                'is_rejected',
                'average_rating',
                'total_reviews'
            )
        }),
    )


@admin.register(PatientProfile)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("user", "gender", "age", "weight", "height")
    search_fields = ("user__username", "user__email")
    list_filter = ("gender",)
