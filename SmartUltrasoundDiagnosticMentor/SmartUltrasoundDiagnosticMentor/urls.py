"""
URL configuration for SmartUltrasoundDiagnosticMentor project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.views.generic.base import RedirectView
from home.views import *
from accounts.views import *
from lifestyle.views import *
from appointment.views import appointment_form, my_appointments, accept_appointment, reject_appointment

urlpatterns = [
    path('favicon.ico', RedirectView.as_view(url='/static/images/logo2.png')),
    path("", home, name="home"),
    path("aboutus/", aboutus, name="aboutus"),
    path("diagnosisform/", diagnosisform, name="diagnosisform"),
    # path("doctors/", doctors, name="doctors"),
    path("doctors/", doctors_list, name="doctors_list"),
    path("doctor/<int:doctor_id>/", doctor_profile, name="doctor_profile"),
    path("submit-review/<int:doctor_id>/", submit_review, name="submit_review"),

    path("signup/", signup_view, name="signup"),
    path('accounts/login/', login_view, name='login'),
    path('accounts/reset/', reset_password_view, name='reset'),
    path("logout/", logout_view, name="logout"),
    path("admin/", admin.site.urls),
    path('profile/', profile_view, name='profile'),
    path('profile/edit/', edit_profile, name='edit_profile'),
    path("dashboard/", dashboard, name="dashboard"),
    path("patient/", patient_dashboard, name="patient_dashboard"),
    path("doctor/", doctor_dashboard, name="doctor_dashboard"),
    path("view_appointment/", view_appointment, name="view_appointment"),
    
    path('appointment/', appointment_form, name='appointment_form_general'),
    path('appointment/<int:doctor_id>/', appointment_form, name='appointment_form_with_id'),    

    path('appointments/', my_appointments, name='my_appointments'),
    path('accept/<int:id>/', accept_appointment, name='accept_appointment'),
    path('reject/<int:id>/', reject_appointment, name='reject_appointment'),
    path('view_ultrasound_images/', view_ultrasound_images, name='view_ultrasound_images'),
    path('view_scan_history/', view_scan_history, name='view_scan_history'),
    path('reports/', view_reports, name='view_reports'),

    path('upload/', upload_image_view, name='upload_image'),
    path('submit-review/<int:doctor_id>/', submit_review, name='submit_review'),
    path("download-pdf/<str:report_id>/", download_pdf, name="download_pdf"),
    path('bookmark/<int:doctor_id>/', toggle_bookmark, name='toggle_bookmark'),
    path('record-bookmark/<str:record_type>/<int:record_id>/', toggle_record_bookmark, name='toggle_record_bookmark'),
    path("diagnosisform/", diagnosisform, name="diagnosisform"),
    
    # Lifestyle System
    path('assessment/', life_assessment, name='life_assessment'),
    path('recommendations/', lifestyle_dashboard, name='lifestyle_dashboard'),

    # Notifications
    path('api/notifications/', get_notifications, name='get_notifications'),
    path('notifications/delete/<int:id>/', delete_notification, name='delete_notification'),
    path('notifications/mark-all-read/', mark_all_notifications_read, name='mark_all_notifications_read'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)