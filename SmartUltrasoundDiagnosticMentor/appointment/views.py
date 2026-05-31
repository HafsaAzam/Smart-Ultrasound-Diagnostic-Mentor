from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import AppointmentForm
from accounts.models import DoctorProfile

from .models import *

@login_required
def appointment_form(request, doctor_id=None):
    user = request.user

    doctor = None
    if doctor_id:
        doctor = get_object_or_404(DoctorProfile, id=doctor_id)
        if doctor.user == user:
            messages.error(request, "you can not book appointment with yourselt")
            return redirect('doctor_profile', doctor_id)

    if request.method == 'POST':
        form = AppointmentForm(request.POST, request=request)

        if form.is_valid():
            appointment = form.save(commit=False)

            appointment.patient = user
            appointment.patient_name = user.get_full_name() or user.username
            appointment.email = user.email
            appointment.status = 'pending'

            if doctor:
                appointment.doctor = doctor

            appointment.save()
            
            from home.models import Notification
            if doctor:
                Notification.objects.create(
                    user=doctor.user,
                    message=f"New appointment request from {appointment.patient_name}."
                )

            messages.success(request, "Your appointment request has been sent. Waiting for doctor's approval.")
            # return redirect('appointment')

        else:
            # Show all form errors as messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)

    else:
        initial_data = {}
        if doctor:
            initial_data['doctor'] = doctor
        
        # Auto-fill phone if available
        try:
            role = user.userprofile.role
            if role == 'doctor':
                if user.doctor_profile.phone:
                    initial_data['phone'] = user.doctor_profile.phone
            elif role == 'patient':
                if hasattr(user, 'patient_profile') and user.patient_profile.phone:
                    initial_data['phone'] = user.patient_profile.phone
        except Exception:
            pass

        form = AppointmentForm(initial=initial_data, request=request)

    return render(request, 'appointment/appointment_form.html', {
        'form': form,
        'doctor': doctor,
    })

@login_required
def appointment_success(request):
    return render('home')

@login_required
def my_appointments(request):
    appointments = Appointment.objects.all()
    return render(request, 'view_appointment.html', {'appointments': appointments})


@login_required
def accept_appointment(request, id):
    appointment = get_object_or_404(Appointment, id=id)
    appointment.status = 'accepted'
    appointment.save()

    from home.models import Notification
    Notification.objects.create(
        user=appointment.patient,
        message=f"Your appointment with Dr. {appointment.doctor.user.username} on {appointment.appointment_date} has been accepted."
    )
    return redirect('view_appointment')


@login_required
def reject_appointment(request, id):
    appointment = get_object_or_404(Appointment, id=id)
    appointment.status = 'rejected'
    appointment.save()

    from home.models import Notification
    Notification.objects.create(
        user=appointment.patient,
        message=f"Your appointment with Dr. {appointment.doctor.user.username} on {appointment.appointment_date} has been rejected."
    )
    return redirect('view_appointment')