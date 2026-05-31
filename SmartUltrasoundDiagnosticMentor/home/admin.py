from django.contrib import admin
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import redirect
from .models import ContactMessage

from home.models import UltrasoundImage, DiagnosticReport, ScanHistory, ContactMessage, DoctorReview
# Register your models here.

@admin.register(DoctorReview)
class DoctorReviewAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'patient', 'rating', 'comment', 'created_at')
    list_filter = ('rating', 'created_at')


@admin.register(UltrasoundImage)
class UltrasoundImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'preview', 'image_date')

    def preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="100" height="100" style="object-fit:cover;" />',
                obj.image.url
            )
        return "No Image"

    preview.short_description = "Ultrasound Image"

@admin.register(DiagnosticReport)
class DiagnosticReportAdmin(admin.ModelAdmin):
    list_display = (
        'report_display_id',
        'user',
        'ultrasound_image_id',
        'ultrasound_preview',
        'age',
        'gender',
        'weight',
        'prediction',
        'report_date',
    )

    def report_display_id(self, obj):
        return f"DX-{obj.id:04d}"

    report_display_id.short_description = "Report ID"
    report_display_id.admin_order_field = 'id'

    readonly_fields = ('report_date', 'ultrasound_preview')

    fieldsets = (
        ('Patient Info', {
            'fields': ('user', 'image', 'ultrasound_preview', 'age', 'gender', 'weight')
        }),
        ('Diagnosis', {
            'fields': ('prediction', 'summary')
        }),
        ('Metadata', {
            'fields': ('report_date',)
        }),
    )

    def ultrasound_image_id(self, obj):
        if obj.image:
            return obj.image.id
        return "-"
    ultrasound_image_id.short_description = "Ultrasound ID"

    def ultrasound_preview(self, obj):
        if not obj.image:
            return "No Image"
        try:
            img_field = obj.image.image
            # 🔥 Critical checks
            if not img_field:
                return "No Image"

            if not img_field.name:
                return "No File"

            if not hasattr(img_field, 'url'):
                return "No URL"

            return format_html(
                '<img src="{}" width="80" height="80" style="object-fit:cover; border-radius:6px;" />',
                img_field.url
            )

        except Exception:
            return "Error Loading Image"
    ultrasound_preview.short_description = "Ultrasound Image"


@admin.register(ScanHistory)
class ScanHistoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_display', 'created_at', 'image_display', 'report_display')
    list_display_links = ('id',)
    ordering = ('-created_at',)

    def user_display(self, obj):
        return obj.user.username
    user_display.short_description = "User"

    def image_display(self, obj):
        if obj.image:
            return f"#{obj.image.id}"
        return "-"
    image_display.short_description = "Ultrasound Image"

    def report_display(self, obj):
        if obj.report:
            return f"DX-{obj.report.id:04d}"
        return "-"
    report_display.short_description = "Diagnostic Report"

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'subject', 'status_label', 'read_action', 'created_at')
    search_fields = ('first_name', 'last_name', 'email', 'subject')
    list_filter = ('created_at', 'is_read')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:message_id>/mark-read/', self.admin_site.admin_view(self.mark_as_read), name='contactmessage_mark_read'),
        ]
        return custom_urls + urls

    def mark_as_read(self, request, message_id):
        msg = ContactMessage.objects.get(id=message_id)
        msg.is_read = True
        msg.save()
        return redirect('admin:home_contactmessage_changelist')

    def change_view(self, request, object_id, form_url='', extra_context=None):
        try:
            msg = ContactMessage.objects.get(id=object_id)
            if not msg.is_read:
                msg.is_read = True
                msg.save()
        except Exception:
            pass
        return super().change_view(request, object_id, form_url, extra_context)

    def status_label(self, obj):
        if obj.is_read:
            return format_html(
                '<span style="color: green; font-weight: bold;">{}</span>',
                'Read'
            )
        return format_html(
        '<span style="color: red; font-weight: bold;">{}</span>',
        'Not Read'
    )
    status_label.short_description = 'Status'

    def read_action(self, obj):
        if not obj.is_read:
            return format_html(
                '<a class="button" style="text-align: center; display: flex; width: 91%; justify-content: center; background-color: var(--secondary); color: white; border-radius: 5px;" href="{}">Mark Read</a>',
                f'{obj.id}/mark-read/'
            )
        return "-"  
    read_action.short_description = 'Action'