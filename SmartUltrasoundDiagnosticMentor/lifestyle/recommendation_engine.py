def calculate_bmi(weight, height):
    """Calculate BMI given weight in kg and height in cm."""
    if not weight or not height:
        return None

    height_m = height / 100

    if height_m <= 0:
        return None

    return round(weight / (height_m * height_m), 1)


def get_bmi_category(bmi):
    if bmi is None:
        return "Unknown"

    if bmi < 18.5:
        return "Underweight"

    if bmi < 25:
        return "Normal"

    if bmi < 30:
        return "Overweight"

    return "Obese"


# =========================
# ALLERGY DATABASE
# =========================

ALLERGY_MAP = {
    'wheat': {
        'avoid': ['Naan', 'Roti', 'Pasta', 'Bakery items'],
        'alternatives': ['Rice', 'Corn flour', 'Millet', 'Buckwheat']
    },

    'dairy': {
        'avoid': ['Milk', 'Lassi', 'Butter', 'Cheese'],
        'alternatives': ['Almond milk', 'Soy milk', 'Oat milk']
    },

    'peanuts': {
        'avoid': ['Peanut butter', 'Mixed nuts', 'Peanut oil'],
        'alternatives': ['Sunflower seeds', 'Pumpkin seeds']
    },

    'gluten': {
        'avoid': ['Wheat', 'Barley', 'Bakery foods'],
        'alternatives': ['Rice', 'Corn', 'Potatoes']
    }
}


# =========================
# PAKISTANI FOOD DATABASE
# =========================

PAKISTANI_HEALTHY_FOODS = [
    "Daal", "Chapati", "Brown rice", "Meat",
    "Fish", "Sabzi", "Yogurt","Fruits","Nuts","Eggs"
]

PAKISTANI_UNHEALTHY_FOODS = [
    "Biryani", "Nihari", "Halwa puri", "Samosa",
    "Pakora", "Burger", "Pizza", "Cold drinks"
]


# =========================
# MAIN ENGINE
# =========================

def generate_full_recommendation(
    health_profile,
    demographics,
    ultrasound_report=None
):

    weight = demographics.get('weight')
    height = demographics.get('height')
    age = demographics.get('age') or 30
    gender = demographics.get('gender') or 'male'

    bmi = calculate_bmi(weight, height)
    bmi_cat = get_bmi_category(bmi)

    conditions = (health_profile.health_conditions or "").lower()
    meals = f"""
    {(health_profile.breakfast or '')}
    {(health_profile.lunch or '')}
    {(health_profile.dinner or '')}
    """.lower()

    ultrasound = (ultrasound_report or "").lower()

    # =========================
    # NUTRITION ADVICE
    # =========================

    nutrition = ""

    if bmi_cat == "Overweight":
        nutrition += (
            "Try reducing oily Pakistani foods like biryani, "
            "nihari, samosa, and sugary drinks. "
        )

    elif bmi_cat == "Underweight":
        nutrition += (
            "Increase healthy calories using dates, nuts, eggs, "
            "banana shakes, and homemade desi foods. "
        )

    else:
        nutrition += (
            "Maintain a balanced Pakistani diet with daal, "
            "chapati, sabzi, yogurt, and fruits. "
        )

    # Fast Food Detection
    if any(food.lower() in meals for food in PAKISTANI_UNHEALTHY_FOODS):
        nutrition += (
            "Avoid frequent fast food and fried street food "
            "to improve digestion and heart health. "
        )

    # Diabetes
    if "diabetes" in conditions:
        nutrition += (
            "For diabetes, avoid excessive white rice, sweets, "
            "mithai, and soft drinks. Choose whole wheat roti "
            "and high-fiber foods. "
        )

    # Hypertension
    if "hypertension" in conditions or "blood pressure" in conditions:
        nutrition += (
            "Reduce salt, achar, chips, and processed foods. "
            "Eat potassium-rich foods like bananas and spinach. "
        )

    # =========================
    # THYROID CONDITIONS
    # =========================

    if "thyroid" in conditions:

        nutrition += (
            "Maintain regular iodine intake through iodized salt "
            "and seafood. Avoid excessive junk food and sugary tea. "
        )

        if "hypothyroidism" in conditions:
            nutrition += (
                "For hypothyroidism, exercise regularly and avoid "
                "too much fried food, bakery items, and sugary drinks. "
            )

        if "hyperthyroidism" in conditions:
            nutrition += (
                "For hyperthyroidism, reduce caffeine, tea, and spicy foods. "
            )

    # =========================
    # ULTRASOUND RELATED CONDITIONS
    # =========================

    if ultrasound:

        # Fatty Liver
        if "fatty liver" in ultrasound:
            nutrition += (
                "Ultrasound indicates fatty liver. Avoid oily foods, "
                "paratha, bakery items, and soft drinks. "
            )

        # Gallstones
        if "gallstones" in ultrasound:
            nutrition += (
                "Gallstones detected. Avoid oily and spicy meals "
                "like karahi, fried chicken, and samosa. "
            )

        # Kidney Stones
        if "kidney stone" in ultrasound:
            nutrition += (
                "Drink plenty of water and reduce salty snacks "
                "and soft drinks to prevent kidney stones. "
            )

        # PCOS
        if "pcos" in ultrasound or "polycystic" in ultrasound:
            nutrition += (
                "PCOS detected. Focus on weight control, low sugar diet, "
                "and regular walking or exercise. "
            )

        # Enlarged Liver
        if "hepatomegaly" in ultrasound:
            nutrition += (
                "Enlarged liver detected. Avoid alcohol and oily foods. "
            )

        # Thyroid Nodules
        if "thyroid nodule" in ultrasound:
            nutrition += (
                "Thyroid nodules detected. Regular thyroid checkups "
                "and endocrinologist consultation are recommended. "
            )

    # =========================
    # ACTIVITY ADVICE
    # =========================

    activity = (
        "Walk at least 30 minutes daily. "
        "Morning walks are especially helpful in Pakistan's climate. "
    )

    if health_profile.activity_level == 'sedentary':
        activity += (
            "Avoid sitting continuously for long periods. "
            "Start with light walking after meals. "
        )

    elif health_profile.activity_level in ['active', 'very_active']:
        activity += (
            "Continue your active routine and include strength training weekly. "
        )

    # =========================
    # SLEEP ADVICE
    # =========================

    sleep_hrs = health_profile.hours_of_sleep

    if sleep_hrs and sleep_hrs < 7:
        sleep = (
            f"You sleep only {sleep_hrs} hours. "
            "Try to get at least 7-8 hours of sleep daily. "
        )

    elif sleep_hrs and sleep_hrs > 9:
        sleep = (
            "Too much sleep can also affect energy levels. "
            "Maintain a proper sleep routine. "
        )

    else:
        sleep = (
            "Maintain 7-8 hours of regular sleep for better health. "
        )

    if 'tea' in (health_profile.other_routine or '').lower():
        sleep += (
            "Avoid strong chai late at night to improve sleep quality. "
        )

    # =========================
    # MENTAL HEALTH
    # =========================

    mental = (
        "Stress management is important. "
        "Try prayer, meditation, family time, and outdoor walks. "
    )

    if age < 40:
        mental += (
            "Avoid excessive screen time and maintain social activities. "
        )

    # =========================
    # SAFETY ALERTS
    # =========================

    safety = ""

    allergies_text = (health_profile.allergies or "").lower()

    if allergies_text and allergies_text not in [
        "none",
        "no",
        "nothing",
        "no allergies"
    ]:

        safety += (
            f"Allergy Alert: Avoid foods related to {health_profile.allergies}. "
        )

        for allergen, advice in ALLERGY_MAP.items():

            if allergen in allergies_text:

                safety += (
                    f"\nAvoid: {', '.join(advice['avoid'])}. "
                )

                safety += (
                    f"\nAlternatives: {', '.join(advice['alternatives'])}. "
                )

    # =========================
    # REASONING
    # =========================

    reasoning = (
        f"Recommendations are generated based on BMI ({bmi}), "
        f"health conditions, ultrasound findings, Pakistani diet habits, "
        f"and lifestyle information."
    )

    # =========================
    # RETURN
    # =========================

    return {
        'bmi': bmi,
        'bmi_category': bmi_cat,
        'nutrition_advice': nutrition,
        'activity_advice': activity,
        'sleep_advice': sleep,
        'mental_health_advice': mental,
        'safety_alerts': safety,
        'reasoning': reasoning
    }