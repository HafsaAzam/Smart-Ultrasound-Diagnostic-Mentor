def navbar_profile(request):
    """Context processor to safely provide navbar profile photo URL."""
    if not request.user.is_authenticated:
        return {'navbar_photo_url': None}

    photo_url = None
    try:
        role = request.user.userprofile.role
        if role == 'doctor':
            dp = request.user.doctor_profile
            if dp.profile_photo:
                photo_url = dp.profile_photo.url
        elif role == 'patient':
            pp = request.user.patient_profile
            if pp.profile_photo:
                photo_url = pp.profile_photo.url
    except Exception:
        pass

    return {'navbar_photo_url': photo_url}
