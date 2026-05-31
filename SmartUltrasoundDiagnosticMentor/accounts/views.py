from django.shortcuts import render, redirect,get_object_or_404
from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import DoctorProfile, PatientProfile, UserProfile
from django.contrib.auth.decorators import login_required


def signup_view(request):
    if request.method == "POST":
        first_name = request.POST.get("f_name", "").strip()
        last_name = request.POST.get("l_name", "").strip()
        username = request.POST.get("email", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("pass2", "")
        role = request.POST.get("role", "")

        # Collect form data to send back on error so user doesn't lose input
        form_data = {
            'f_name': first_name,
            'l_name': last_name,
            'email': email,
            'role': role,
            'doctor_gender': request.POST.get("doctor_gender", ""),
            'doctor_age': request.POST.get("doctor_age", ""),
            'prof_years': request.POST.get("prof_years", ""),
            'doctor_degrees': request.POST.get("doctor_degrees", ""),
            'doctor_weight': request.POST.get("doctor_weight", ""),
            'patient_gender': request.POST.get("patient_gender", ""),
            'age': request.POST.get("age", ""),
            'weight': request.POST.get("weight", ""),
        }

        # --- Validate BEFORE creating anything in the database ---

        # Required fields check
        if not all([first_name, last_name, email, password, confirm_password, role]):
            messages.error(request, "All required fields must be filled.")
            return render(request, "accounts/signup.html", {'form_data': form_data})

        # Password match
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, "accounts/signup.html", {'form_data': form_data})

        # Password strength
        import re
        if len(password) < 8 or not re.search(r'[A-Z]', password) or not re.search(r'[a-z]', password) or not re.search(r'\d', password) or not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            messages.error(request, "Password must be at least 8 characters long, include a capital letter, a small letter, a number, and a special symbol.")
            return render(request, "accounts/signup.html", {'form_data': form_data})

        # Check if email already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, "Email already registered.")
            return render(request, "accounts/signup.html", {'form_data': form_data})

        # Role-specific validation BEFORE creating user
        if role == "doctor":
            gender = request.POST.get("doctor_gender")
            age = request.POST.get("doctor_age")
            experience = request.POST.get("prof_years")
            degrees = request.POST.get("doctor_degrees")
            degree_document = request.FILES.get("degree_document")

            if not all([gender, age, experience, degrees, degree_document]):
                messages.error(request, "All doctor profile fields are required (Gender, Age, Experience, Degrees, Degree Document).")
                return render(request, "accounts/signup.html", {'form_data': form_data})

            try:
                int(age)
                float(request.POST.get("doctor_weight") or 0.0)
                int(experience)
            except (ValueError, TypeError):
                messages.error(request, "Invalid numeric value for Age, Weight, or Experience.")
                return render(request, "accounts/signup.html", {'form_data': form_data})

        elif role == "patient":
            gender = request.POST.get("patient_gender")
            age = request.POST.get("age")
            if not all([gender, age]):
                messages.error(request, "Gender and Age are required for patients.")
                return render(request, "accounts/signup.html", {'form_data': form_data})

            try:
                int(age)
                float(request.POST.get("weight") or 0.0)
            except (ValueError, TypeError):
                messages.error(request, "Invalid numeric value for Age or Weight.")
                return render(request, "accounts/signup.html", {'form_data': form_data})
        else:
            messages.error(request, "Please select a valid role.")
            return render(request, "accounts/signup.html", {'form_data': form_data})

        # --- All validations passed, now create user + profile atomically ---
        from django.db import transaction
        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                )
                UserProfile.objects.create(user=user, role=role)

                if role == "doctor":
                    DoctorProfile.objects.create(
                        user=user,
                        gender=request.POST.get("doctor_gender"),
                        age=int(request.POST.get("doctor_age")),
                        weight=float(request.POST.get("doctor_weight") or 0.0),
                        experience=int(request.POST.get("prof_years")),
                        degrees=request.POST.get("doctor_degrees"),
                        degree_document=request.FILES.get("degree_document"),
                    )
                    messages.success(
                        request,
                        "Doctor account created successfully! You can now use our platform as a patient while your medical profile is being verified by the admin."
                    )

                elif role == "patient":
                    PatientProfile.objects.create(
                        user=user,
                        gender=request.POST.get("patient_gender"),
                        age=int(request.POST.get("age")),
                        weight=float(request.POST.get("weight") or 0.0),
                    )

                login(request, user)
                return redirect("home")

        except Exception:
            messages.error(request, "An error occurred while creating your account. Please try again.")
            return render(request, "accounts/signup.html", {'form_data': form_data})

    return render(request, "accounts/signup.html")


def login_view(request):
    next_url = request.GET.get('next')

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        next_url = request.POST.get("next")

        if not User.objects.filter(username=username).exists():
            messages.error(request, "Account does not exist")
        else:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                if user.is_superuser or user.is_staff:
                    messages.error(request, "Admins can only log in through the admin panel.")
                else:
                    login(request, user)
                    if next_url:
                        return redirect(next_url)
                    return redirect("home")
            else:
                messages.error(request, "Invalid password")

    return render(request, "accounts/login.html", {"next": next_url})

def reset_password_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password1 = request.POST.get("pass")
        password2 = request.POST.get("pass2")

        if not email or not password1 or not password2:
            messages.error(request, "All fields are required")
            return redirect("reset")

        # Check if passwords match
        if password1 != password2:
            messages.error(request, "Passwords do not match")
            return redirect("reset")

        try:
            user = User.objects.get(username=email)
            user.set_password(password1)  # securely hash password
            user.save()

            messages.success(request, "Password reset successful. Please login.")
            return redirect("login")

        except User.DoesNotExist:
            messages.error(request, "User with this email does not exist")
            return redirect("reset")

    return render(request, "accounts/reset.html")

def logout_view(request):
    logout(request)
    return redirect("login")

@login_required
def profile_view(request):
    role = request.user.userprofile.role

    if role == "doctor":
        profile = DoctorProfile.objects.get(user=request.user)
        return render(request, "accounts/doctor_profile.html", {"profile": profile})

    elif role == "patient":
        profile = PatientProfile.objects.get(user=request.user)
        return render(request, "accounts/patient_profile.html", {"profile": profile})

@login_required
def edit_profile(request):
    role = request.user.userprofile.role

    if role == "doctor":
        profile = DoctorProfile.objects.get(user=request.user)

        if request.method == "POST":
            profile.gender = request.POST.get("gender")
            
            # Handle numerical fields safely
            try:
                age = request.POST.get("age")
                if age:
                    profile.age = int(age)
                
                weight = request.POST.get("weight")
                profile.weight = float(weight) if weight else None
                
                height = request.POST.get("height")
                profile.height = float(height) if height else None
                
                experience = request.POST.get("experience")
                if experience:
                    profile.experience = int(experience)
            except (ValueError, TypeError):
                messages.error(request, "Invalid numeric value provided.")
                return render(request, "accounts/edit_doctor_profile.html", {"profile": profile})

            profile.phone = request.POST.get("phone")
            profile.office_location = request.POST.get("office_location")
            profile.degrees = request.POST.get("degrees")
            profile.is_available = 'is_available' in request.POST
        
        # ✅ Profile photo (doctor image)
            if request.FILES.get("profile_photo"):
                profile.profile_photo = request.FILES.get("profile_photo")
            
        # ✅ Degree document
            if request.FILES.get("degree_document"):
                profile.degree_document = request.FILES.get("degree_document")
            profile.save()
            return redirect("profile")

        return render(request, "accounts/edit_doctor_profile.html", {"profile": profile})


    elif role == "patient":
        profile = PatientProfile.objects.get(user=request.user)

        if request.method == "POST":
            profile.gender = request.POST.get("gender")
            
            # Handle numerical fields safely
            try:
                age = request.POST.get("age")
                if age:
                    profile.age = int(age)
                
                weight = request.POST.get("weight")
                profile.weight = float(weight) if weight else None
                
                height = request.POST.get("height")
                profile.height = float(height) if height else None
            except (ValueError, TypeError):
                messages.error(request, "Invalid numeric value provided.")
                return render(request, "accounts/edit_patient_profile.html", {"profile": profile})
            
            if request.FILES.get("profile_photo"):
                profile.profile_photo = request.FILES.get("profile_photo")
            
            profile.save()
            return redirect("profile")

        return render(request, "accounts/edit_patient_profile.html", {"profile": profile})
