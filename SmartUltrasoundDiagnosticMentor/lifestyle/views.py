from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import HealthProfile, LifestyleRecommendation
from .forms import HealthProfileForm
from .recommendation_engine import generate_full_recommendation

@login_required
def life_assessment(request):
    health_profile, created = HealthProfile.objects.get_or_create(user=request.user)
    role = request.user.userprofile.role
    if role == 'doctor':
        p = request.user.doctor_profile
    else:
        p = request.user.patient_profile

    if request.method == "POST":
        form = HealthProfileForm(request.POST, instance=health_profile)
        if form.is_valid():
            # Save to HealthProfile
            hp = form.save()
            
            # Sync back to primary profile to keep systems aligned
            p.age = hp.age if hp.age else p.age
            p.gender = hp.gender if hp.gender else p.gender
            p.weight = hp.weight if hp.weight else p.weight
            p.height = hp.height if hp.height else p.height
            p.save()

            # Pre-generate first recommendation so dashboard knows assessment was made
            demographics = {
                'age': hp.age,
                'gender': hp.gender,
                'weight': hp.weight,
                'height': hp.height
            }
            rec_data = generate_full_recommendation(hp, demographics)
            LifestyleRecommendation.objects.create(
                user=request.user,
                bmi=rec_data['bmi'],
                bmi_category=rec_data['bmi_category'],
                nutrition_advice=rec_data['nutrition_advice'],
                activity_advice=rec_data['activity_advice'],
                sleep_advice=rec_data['sleep_advice'],
                mental_health_advice=rec_data['mental_health_advice'],
                safety_alerts=rec_data['safety_alerts'],
                reasoning=rec_data['reasoning']
            )

            messages.success(request, "Health Profile updated! Now viewing your personalized recommendations.")
            return redirect('lifestyle_dashboard')
    else:
        # Pre-fill HealthProfile if its internal demographics are missing but exists in primary profile
        if not health_profile.age: health_profile.age = p.age
        if health_profile.gender in [None, '']: health_profile.gender = p.gender
        if not health_profile.weight: health_profile.weight = p.weight
        if not health_profile.height: health_profile.height = p.height
        
        form = HealthProfileForm(instance=health_profile)
    
    return render(request, "lifestyle_assessment.html", {"form": form})

@login_required
def lifestyle_dashboard(request):
    # Check if user has EVER made an assessment (implied by having at least one recommendation)
    if not LifestyleRecommendation.objects.filter(user=request.user).exists():
        return redirect('life_assessment')

    try:
        health_profile = HealthProfile.objects.get(user=request.user)
    except HealthProfile.DoesNotExist:
        return redirect('life_assessment')

    # Use demographics from HealthProfile (captured in assessment)
    demographics = {
        'age': health_profile.age,
        'gender': health_profile.gender,
        'weight': health_profile.weight,
        'height': health_profile.height
    }

    # Generate recommendation
    r = generate_full_recommendation(health_profile, demographics)

    # Gauge rotation (12 to 40 BMI -> -90 to 90 deg)
    bmi = r.get('bmi') or 18
    bmi_rotation = (bmi - 26) * (180/28) 
    if bmi_rotation < -90: bmi_rotation = -90
    if bmi_rotation > 90: bmi_rotation = 90

    context = {
        'r': r,
        'hp': health_profile,
        'bmi_rotation': bmi_rotation,
    }
    return render(request, "lifestyle_dashboard.html", context)
