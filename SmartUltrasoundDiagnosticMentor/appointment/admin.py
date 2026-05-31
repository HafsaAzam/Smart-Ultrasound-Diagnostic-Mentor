from django.contrib import admin
from .models import Appointment

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('patient_name', 'doctor', 'appointment_date', 'appointment_time', 'status')
    list_filter = ('doctor', 'status', 'appointment_date')
    actions = ['accept_appointments', 'reject_appointments']

    # Show only appointments for logged-in doctor
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Filter by doctor linked to logged-in user
        return qs.filter(doctor__user=request.user)

    # Admin actions
    def accept_appointments(self, request, queryset):
        updated = queryset.update(status='accepted')
        for appointment in queryset:
            appointment.send_email('accepted')  # we'll define this method
        self.message_user(request, f"{updated} appointments accepted.")
    accept_appointments.short_description = "Accept selected appointments"

    def reject_appointments(self, request, queryset):
        updated = queryset.update(status='rejected')
        for appointment in queryset:
            appointment.send_email('rejected')
        self.message_user(request, f"{updated} appointments rejected.")
    reject_appointments.short_description = "Reject selected appointments"