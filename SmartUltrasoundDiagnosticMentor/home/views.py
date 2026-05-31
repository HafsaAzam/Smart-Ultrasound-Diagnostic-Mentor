from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
# pyrefly: ignore [missing-import]
from .models import Notification

from django.contrib import messages
from django.http import HttpResponse
from django.http import JsonResponse
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Q

from django.conf import settings
from django.core.files.base import ContentFile

from accounts.models import *
from home.models import *
from appointment.models import Appointment
from home.forms import *
from ml_utils.features import extract_hybrid_features
from tensorflow.keras.models import load_model

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

import os
import cv2
import numpy as np
import joblib
# Model Paths
MODEL_DIR = os.path.join(settings.BASE_DIR, "ml_models")

CNN_MODEL_PATH = os.path.join(MODEL_DIR, "cnn_feature_extractor.keras")
PIPELINE_PATH = os.path.join(MODEL_DIR, "hybrid_ml_pipeline.pkl")

# Load Models Safely
cnn_model = None
model = None
pt = None
pca = None
label_encoder = None

try:
    # Load CNN model
    if os.path.exists(CNN_MODEL_PATH):
        cnn_model = load_model(CNN_MODEL_PATH)
    else:
        print(f" CNN model not found at: {CNN_MODEL_PATH}")

    # Load ML pipeline
    if os.path.exists(PIPELINE_PATH):
        data = joblib.load(PIPELINE_PATH)
        model = data.get("pipeline")
        pt = data.get("power_transformer")
        pca = data.get("pca")
        label_encoder = data.get("label_encoder")
        print(" Models loaded successfully")
    else:
        print(f" Pipeline file not found at: {PIPELINE_PATH}")

except Exception as e:
    print(f"Model loading failed: {e}")


def is_effective_doctor(user):
    """Returns True only if user is a verified, non-rejected doctor."""
    try:
        if user.userprofile.role == 'doctor':
            prof = user.doctor_profile
            return prof.is_verified and not prof.is_rejected
    except Exception:
        pass
    return False

@login_required
def get_notifications(request):
    # Only show unread notifications in the dropdown
    notifications = Notification.objects.filter(user=request.user, is_read=False).order_by('-created_at')[:10]

    data = [{
        'id': n.id,
        'message': n.message,
        'is_read': n.is_read,
        'created_at': n.created_at.strftime('%Y-%m-%d %H:%M'),
    } for n in notifications]

    return JsonResponse({
        'notifications': data,
        'unread_count': Notification.objects.filter(user=request.user, is_read=False).count()
    })


@login_required
@require_POST
def delete_notification(request, id):
    try:
        notif = Notification.objects.get(id=id, user=request.user)
        notif.delete()
        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


@login_required
@require_POST
def mark_all_notifications_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({"success": True})

# Home
def home(request):
    profile = None

    if request.user.is_authenticated:
        try:
            profile = PatientProfile.objects.get(user=request.user)
        except PatientProfile.DoesNotExist:
            profile = None

    if request.method == "POST":
        if not request.user.is_authenticated:
            messages.error(request, "Please log in to send a contact message.")
            return redirect("/accounts/login/?next=/#contact")

        first_name = request.POST.get("first_name", "")
        last_name = request.POST.get("last_name", "")
        email = request.POST.get("email", "")
        subject = request.POST.get("subject", "")
        message = request.POST.get("message", "")

        if first_name and email and message:
            ContactMessage.objects.create(
                first_name=first_name,
                last_name=last_name,
                email=email,
                subject=subject,
                message=message
            )
            messages.success(request, "Your message has been sent successfully. We will get back to you soon.")
        else:
            messages.error(request, "Please fill in all required fields.")
            
        return redirect("/#contact")

    return render(request, "index.html", {"profile": profile})

def aboutus(request):
    return render(request, "aboutus.html")

@login_required
def diagnosisform(request):
    user = request.user
    role = user.userprofile.role
    context = {}
    
    if role == 'patient':
        try:
            profile = user.patient_profile
            context['profile'] = profile
            context['name'] = user.get_full_name() or user.username
        except Exception:
            pass
    elif role == 'doctor':
        context['name'] = user.get_full_name() or user.username
        # doctor's age, gender, weight should be empty in form
        
    return render(request, "diagnosis_form.html", context)

def doctors(request):
    return render(request, "doctors.html")
# Doctor List Page
def doctors_list(request):
    doctors_qs = DoctorProfile.objects.filter(is_verified=True, is_rejected=False)

    if request.user.is_authenticated:
        bookmarked_ids = set(Bookmark.objects.filter(
            user=request.user
        ).values_list('doctor_id', flat=True))

        # We'll create a list and sort it in memory to keep it simple, 
        # or use annotation for DB-level sorting which is better.
        from django.db.models import Exists, OuterRef
        bookmarked_qs = Bookmark.objects.filter(user=request.user, doctor=OuterRef('pk'))
        doctors = doctors_qs.annotate(is_bookmarked=Exists(bookmarked_qs)).order_by('-is_bookmarked', 'user__first_name')
    else:
        doctors = doctors_qs.order_by('user__first_name')
        for doc in doctors:
            doc.is_bookmarked = False

    return render(request, 'doctors.html', {'doctors': doctors}) 


@login_required
def doctor_profile(request, doctor_id):
    doctor = get_object_or_404(DoctorProfile, id=doctor_id, is_verified=True, is_rejected=False)

    if request.user.is_authenticated:
        is_bookmarked = Bookmark.objects.filter(
            user=request.user, doctor=doctor
        ).exists()
        doctor.is_bookmarked = is_bookmarked
    else:
        doctor.is_bookmarked = False

    return render(request, 'doctor_profile.html', {'doctor': doctor})
    
# Submit Review
@login_required
def submit_review(request, doctor_id):
    doctor = get_object_or_404(DoctorProfile, id=doctor_id)

    if request.method == "POST":
        if not request.user.is_authenticated:
            messages.error(request, "You must be logged in to leave a review.")
            return redirect("login")
            
        if request.user == doctor.user:
            messages.error(request, "You cannot review yourself.")
            return redirect("doctor_profile", doctor_id=doctor.id)
            
        now = timezone.localtime()
        appointments = Appointment.objects.filter(
            patient=request.user, 
            doctor=doctor, 
            status='accepted'
        )
        
        can_review = False
        for appt in appointments:
            if hasattr(appt, 'appointment_time') and hasattr(appt, 'appointment_date'):
                appt_dt = timezone.make_aware(datetime.combine(appt.appointment_date, appt.appointment_time))
                finish_time = appt_dt + timedelta(hours=1)
                time_diff = finish_time + timedelta(hours=48)
                
                if finish_time <= now <= time_diff:
                    can_review = True
                    break
        
        if not can_review:
            messages.error(request, "you can add review after booking appointment and finishing of appointment")
            return redirect("doctor_profile", doctor_id=doctor.id)
            
        rating = int(request.POST.get("rating", 0))
        if rating < 1 or rating > 5:
            messages.error(request, "Please provide a valid rating.")
            return redirect("doctor_profile", doctor_id=doctor.id)
            
        comment = request.POST.get("comment", "")

        DoctorReview.objects.create(
            doctor=doctor,
            patient=request.user,
            rating=rating,
            comment=comment
        )

        # Update rating
        reviews = doctor.reviews.all()
        total = reviews.count()

        if total > 0:
            avg = sum(r.rating for r in reviews) / total
            doctor.average_rating = round(avg, 1)
            doctor.total_reviews = total
            doctor.save()
            
        messages.success(request, "Review submitted successfully.")

    return redirect("doctor_profile", doctor_id=doctor.id)

def update_doctor_rating(doctor):
    reviews = doctor.reviews.all()
    total = reviews.count()

    if total > 0:
        avg = sum(r.rating for r in reviews) / total
        doctor.average_rating = round(avg, 1)
        doctor.total_reviews = total
        doctor.save()

@login_required
def toggle_bookmark(request, doctor_id):
    doctor = DoctorProfile.objects.get(id=doctor_id)

    bookmark, created = Bookmark.objects.get_or_create(
        user=request.user,
        doctor=doctor
    )

    if not created:
        bookmark.delete()
        return JsonResponse({'saved': False})
    
    return JsonResponse({'saved': True})


@login_required
@require_POST
def toggle_record_bookmark(request, record_type, record_id):
    """Toggle bookmark for a specific record row (appointment/report/image/scan)."""
    VALID_TYPES = ['appointment', 'report', 'image', 'scan']
    if record_type not in VALID_TYPES:
        return JsonResponse({'error': 'Invalid record type'}, status=400)

    # Build a human-readable label
    label = f"{record_type.title()} #{record_id}"
    try:
        if record_type == 'appointment':
            from appointment.models import Appointment
            obj = Appointment.objects.get(id=record_id)
            label = f"Appointment on {obj.appointment_date} at {obj.appointment_time}"
        elif record_type == 'report':
            obj = DiagnosticReport.objects.get(id=record_id)
            label = f"Report DX-{obj.id:04d} — {obj.prediction} ({obj.report_date.strftime('%Y-%m-%d')})"
        elif record_type == 'image':
            obj = UltrasoundImage.objects.get(id=record_id)
            label = f"Image #{obj.id} — {obj.image_date.strftime('%Y-%m-%d')}"
        elif record_type == 'scan':
            obj = ScanHistory.objects.get(id=record_id)
            label = f"Scan #{obj.user_scan_number} — {obj.created_at.strftime('%Y-%m-%d')}"
    except Exception:
        pass

    bookmark, created = RecordBookmark.objects.get_or_create(
        user=request.user,
        record_type=record_type,
        record_id=record_id,
        defaults={'label': label}
    )

    if not created:
        bookmark.delete()
        return JsonResponse({'bookmarked': False})

    bookmark.label = label
    bookmark.save()
    return JsonResponse({'bookmarked': True})
# Dashboard redirect
@login_required
def dashboard(request):
    role = request.user.userprofile.role

    if role == "doctor":
        # Check if verified. If rejected or not verified, treat as patient.
        doctor_prof = DoctorProfile.objects.get(user=request.user)
        if doctor_prof.is_verified and not doctor_prof.is_rejected:
            return redirect("doctor_dashboard")
        else:
            return redirect("patient_dashboard")
    else:
        return redirect("patient_dashboard")


# Patient Dashboard
@login_required
def patient_dashboard(request):
    user = request.user

    appointments_count = Appointment.objects.filter(patient=user).count()
    scan_count = ScanHistory.objects.filter(user=user).count()
    reports_count = DiagnosticReport.objects.filter(user=user).count()
    
    # Bookmarks
    record_bookmarks = RecordBookmark.objects.filter(user=user).order_by('-created_at')
    doctor_bookmarks = Bookmark.objects.filter(user=user).select_related('doctor', 'doctor__user')

    context = {
        "appointments_count": appointments_count or 0,
        "scan_count": scan_count or 0,
        "reports_count": reports_count or 0,
        "comparisons_count": 0,
        "bookmarks": record_bookmarks,
        "doctor_bookmarks": doctor_bookmarks,
    }

    return render(request, "patient_dashboard.html", context)


# Doctor Dashboard
@login_required
def doctor_dashboard(request):

    role = request.user.userprofile.role

    if role == "doctor":
        # Get doctor profile
        doctor_prof = get_object_or_404(DoctorProfile, user=request.user)
        
        # Security: if not verified or is rejected, they shouldn't see this dashboard
        if not doctor_prof.is_verified or doctor_prof.is_rejected:
            messages.warning(request, "Your doctor account is not verified yet. You are currently viewing the patient features.")
            return redirect("patient_dashboard")

        doctor_appointments = Appointment.objects.filter(
        doctor=doctor_prof
        )

        scan_count = ScanHistory.objects.filter(
            user=request.user
        ).count()

        # Get reports created by this doctor
        reports_count = DiagnosticReport.objects.filter(
            user=request.user
        ).count()

    # Bookmarks
    record_bookmarks = RecordBookmark.objects.filter(user=request.user).order_by('-created_at')
    doctor_bookmarks = Bookmark.objects.filter(user=request.user).select_related('doctor', 'doctor__user')

    context = {
        "total_appointments": doctor_appointments.count() or 0,
        "pending": doctor_appointments.filter(status='pending').count() or 0,
        "accepted": doctor_appointments.filter(status='accepted').count() or 0,
        "rejected": doctor_appointments.filter(status='rejected').count() or 0,
        "appointments": doctor_appointments or 0,
        "scan_count": scan_count or 0,
        "reports_count": reports_count or 0,
        "comparisons_count": 0,
        "bookmarks": record_bookmarks,
        "doctor_bookmarks": doctor_bookmarks,
    }

    return render(request, "doctor_dashboard.html", context)


# Update Appointment Status
@login_required
def update_appointment_status(request, id, status):
    appointment = get_object_or_404(Appointment, id=id)

    if request.user == appointment.doctor:
        appointment.status = status
        appointment.save()

    return redirect('doctor_dashboard')


# View Appointments
@login_required
def view_appointment(request):
    if is_effective_doctor(request.user):
        doctor_prof = DoctorProfile.objects.get(user=request.user)
        appointments = Appointment.objects.filter(
            Q(doctor=doctor_prof) | Q(patient=request.user)
        ).order_by('-appointment_date')
        role = 'doctor'
    else:
        appointments = Appointment.objects.filter(patient=request.user).order_by('-appointment_date')
        role = 'patient'

    bookmarked_ids = set(RecordBookmark.objects.filter(
        user=request.user, record_type='appointment'
    ).values_list('record_id', flat=True))

    return render(request, 'view_appointment.html', {
        "appointments": appointments,
        "role": role,
        "bookmarked_ids": bookmarked_ids,
    })

@login_required
def view_ultrasound_images(request):
    images = UltrasoundImage.objects.filter(
        patient=request.user
    ).order_by('-image_date')

    for img in images:
        report = DiagnosticReport.objects.filter(image=img).first()
        if report and report.patient_name:
            img.display_name = report.patient_name
        else:
            img.display_name = request.user.username

    bookmarked_ids = set(RecordBookmark.objects.filter(
        user=request.user, record_type='image'
    ).values_list('record_id', flat=True))

    return render(request, 'view_ultrasoundImages.html', {
        "images": images,
        "bookmarked_ids": bookmarked_ids,
    })

@login_required
def view_reports(request):
    if is_effective_doctor(request.user):
        doctor_prof = DoctorProfile.objects.get(user=request.user)
        reports = DiagnosticReport.objects.filter(
            image__doctor=doctor_prof
        ).order_by('-report_date')
        role = 'doctor'
    else:
        reports = DiagnosticReport.objects.filter(
            user=request.user
        ).order_by('-report_date')
        role = 'patient'

    bookmarked_ids = set(RecordBookmark.objects.filter(
        user=request.user, record_type='report'
    ).values_list('record_id', flat=True))

    return render(request, 'view_reports.html', {
        "reports": reports,
        "role": role,
        "bookmarked_ids": bookmarked_ids,
    })

@login_required
def view_scan_history(request):
    history = ScanHistory.objects.filter(
        user=request.user
    ).order_by('-created_at')

    for item in history:
        if item.report and item.report.patient_name:
            item.display_name = item.report.patient_name
        else:
            item.display_name = request.user.username

    bookmarked_ids = set(RecordBookmark.objects.filter(
        user=request.user, record_type='scan'
    ).values_list('record_id', flat=True))

    return render(request, 'view_scan_history.html', {
        "history": history,
        "bookmarked_ids": bookmarked_ids,
    })
    


#check file  type:
def checktype(uploaded_file, request, img_path):

    allowed_extensions = ['.jpg', '.jpeg', '.png']

    ext = os.path.splitext(uploaded_file.name)[1].lower()

    if ext == '.txt':
        messages.warning(request, "❌ File not supported. Please upload an image file.")
        return False

    if ext not in allowed_extensions:
        messages.warning(request, "❌ Unsupported format. Please upload JPG or PNG image.")
        return False

    #  SAFE IMAGE LOAD
    img = cv2.imread(str(img_path))
    if img is None: return False

    # 1. Check if the image is actually grayscale-ish
    # Real photos have high variance between color channels; Ultrasounds do not.
    b, g, r = cv2.split(img)
    if not (np.array_equal(b, g) and np.array_equal(g, r)):
        # If not perfectly grayscale, check how "colorful" it is
        if np.mean(np.std([b, g, r], axis=0)) > 10: # Threshold for color variance
            messages.warning(request, "⚠ Please upload a grayscale Ultrasound image.")
            return False

    # 2. Refined Intensity Check
    # Ultrasounds are mostly dark. A mean intensity > 150 is usually too bright.
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    mean_val = np.mean(gray)
    if mean_val > 150 or mean_val < 10:
        messages.error(request, "⚠ Please upload a grayscale Ultrasound image.")
        return False

    return True


#upload img 
@login_required
def upload_image_view(request):

    if not request.user.is_authenticated:
        return redirect('login')

    if request.method == "POST" and request.FILES.get('image'):

        uploaded_file = request.FILES['image']
        temp_instance = UltrasoundImage(image=uploaded_file)
        # 1. Save Image to DB
        img_record = UltrasoundImage.objects.create(
            patient=request.user,
            image=uploaded_file
        )

        # Read image
        image = cv2.imread(img_record.image.path)

        if image is None:
            messages.error(request, "Could not process image.")
            return redirect('home')
        if not checktype(uploaded_file, request, img_record.image.path):
            return redirect('home')

        # --- UPDATED ML PIPELINE ---
        try:
            
            raw_features = extract_hybrid_features(img_record.image.path)
            raw_features = raw_features.reshape(1, -1)
            pt_features = pt.transform(raw_features)
            pca_features = pca.transform(pt_features)
            probs = model.predict_proba(pca_features)[0]
            top_idx = np.argmax(probs)
            prediction_label = label_encoder.inverse_transform([top_idx])[0]
            # Confidence summary
            summary_text = (
                f"AI Analysis Result: {prediction_label}.\n"
                f"Probabilities => Benign:{probs[0]*100:.2f}%, "
                f"Malignant:{probs[1]*100:.2f}%, "
                f"Normal:{probs[2]*100:.2f}%"
            )

        except Exception as e:
            print(f"ML Pipeline Error: {e}")
            prediction_label = "INCONCLUSIVE"
            summary_text = f"Error during AI analysis: {str(e)}"
            probs = [0.0, 0.0, 0.0]

        # --- END PIPELINE ---
        system_count = DiagnosticReport.objects.count() + 1
        user_count = DiagnosticReport.objects.filter(user=request.user).count() + 1
        new_report = DiagnosticReport.objects.create(
             user=request.user,
             image=img_record,
             patient_name=request.POST.get("name") or request.user.get_full_name() or request.user.username,
             prediction=prediction_label,
             gender=request.POST.get("patient_gender", "Not Specified"),
             age=request.POST.get("age") or 0,
             weight=request.POST.get("weight") or 0.0,
             summary=summary_text,
             user_report_number=user_count
             )
        new_report.report_code = f"DX-{system_count:04d}"
        new_report.save()

        # Create scan history entry
        user_scan_count = ScanHistory.objects.filter(user=request.user).count() + 1
        ScanHistory.objects.create(
            user=request.user,
            image=img_record,
            report=new_report,
            user_scan_number=user_scan_count
        )

        return render(request, "upload_result.html", {
            "report_id": new_report.id,
            "report_display_id": new_report.report_code,
            "user_report_no": new_report.user_report_number,  
            "passed_name": new_report.patient_name,
            "prediction": prediction_label,
            "gender": new_report.gender,
            "age": new_report.age,
            "weight": new_report.weight,
            "summary": new_report.summary,
            "image_url": img_record.image.url,
            "date_time": new_report.report_date,
            })

    return redirect('home')

@login_required
def download_pdf(request, report_id):

    report = get_object_or_404(DiagnosticReport, id=report_id)

    response = HttpResponse(content_type='application/pdf')

    user_name = report.patient_name or report.user.get_full_name() or report.user.username
    filename = f"Diagnostic_Report_{user_name}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    # ---------------- HEADER ----------------
    p.setFillColorRGB(0.08, 0.26, 0.46)
    p.rect(0, 750, width, 100, fill=1)

    logo_path = os.path.join(settings.BASE_DIR, 'static/images/logo2.png')
    if os.path.exists(logo_path):
        p.drawImage(logo_path, 40, 765, width=60, height=60, mask='auto')

    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 20)
    p.drawString(110, 790, "Smart Ultrasound Diagnostic Mentor")

    p.setFont("Helvetica", 10)
    p.drawString(110, 775, "AI-powered Thyroid Nodule Analysis")

    # ---------------- PATIENT INFO ----------------
    p.setFillColor(colors.black)
    p.setFont("Helvetica-Bold", 11)
    p.drawString(50, 720, f"PATIENT: {user_name.upper()}")

    # SYSTEM DIAGNOSTIC ID (GLOBAL)
    diagnostic_id = report.report_code

    # USER REPORT COUNT (HOW MANY REPORTS USER GENERATED)
    user_report_no = DiagnosticReport.objects.filter(
        user=report.user,
        id__lte=report.id
    ).count()

    date_time = report.report_date.strftime('%Y-%m-%d %H:%M:%S')

    p.setFont("Helvetica", 10)
    p.drawString(
        50, 705,
        f"Diagnosis ID: {diagnostic_id} | User Report #: {user_report_no}"
    )
    p.drawRightString(550, 720, f"Date: {date_time}")

    p.line(50, 695, 550, 695)

    # ---------------- IMAGE ----------------
    current_y = 670
    p.setFont("Helvetica-Bold", 12)
    p.drawCentredString(width/2, current_y, "Analyzed Ultrasound Scan:")

    img_path = report.image.image.path if report.image and report.image.image else None
    img_w, img_h = 300, 220

    if img_path and os.path.exists(img_path):
        p.drawImage(img_path, (width - img_w)/2, current_y - 230, width=img_w, height=img_h)
        current_y -= 250
    else:
        p.setFont("Helvetica-Oblique", 10)
        p.drawCentredString(width/2, current_y - 20, "[Scan Image Not Found]")
        current_y -= 50

    # ---------------- RESULTS ----------------
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, current_y, "Diagnostic Results:")
    current_y -= 25

    pred = report.prediction or "Unknown"
    gender = report.gender
    age = report.age
    weight = report.weight

    data_items = [
        ("AI Prediction", pred.upper()),
        ("Patient Gender", gender),
        ("Patient Age", f"{age} Years"),
        ("Body Weight", f"{weight} kg")
    ]

    row_y = current_y - 40
    p.setFont("Helvetica", 11)

    for label, value in data_items:
        p.setFillColor(colors.black)
        p.drawString(60, row_y, label)

        if "MALIGNANT" in value:
            p.setFillColor(colors.red)
        elif "BENIGN" in value:
            p.setFillColor(colors.green)
        else:
            p.setFillColor(colors.black)

        p.setFont("Helvetica-Bold", 11)
        p.drawString(260, row_y, value)

        p.setFont("Helvetica", 11)
        p.setStrokeColor(colors.lightgrey)
        p.line(50, row_y - 5, 550, row_y - 5)

        row_y -= 25

    # ---------------- SUMMARY ----------------
    current_y = row_y - 20
    p.setFillColor(colors.black)
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, current_y, "Clinical Summary:")

    p.setFont("Helvetica", 10)
    p.drawString(50, current_y - 20, f"AI Analysis predicts {pred.lower()} condition.")

    # ---------------- FOOTER ----------------
    p.setFont("Helvetica-Oblique", 8)
    p.setFillColor(colors.grey)
    p.drawCentredString(
        width/2,
        40,
        "Disclaimer: AI-generated report, verify with radiologist"
    )

    p.showPage()
    p.save()

    return response
