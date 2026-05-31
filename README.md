# Smart Ultrasound Diagnostic Mentor

# Overview
Smart Ultrasound Diagnostic Mentor is an AI-powered healthcare web application designed for the early detection of thyroid nodules using ultrasound imaging.It integrates machine learning, medical image processing, and a full-stack web system to support both patients and healthcare professionals in diagnosis, reporting, and healthcare management.

# AI Model Highlights
Hybrid feature extraction using:
. MobileNetV2 (deep learning features)
. LBP (texture analysis)
. GLCM (statistical texture features)
. Dimensionality reduction using PCA
. Ensemble classification:
. Random Forest
. XGBoost
. Logistic Regression (meta-learner)

# Achieved:
. 97% Accuracy
. 98% Sensitivity
. 98% F1-Score

# Key Features
. AI Diagnosis: Classifies ultrasound images into:
      . Benign
      . Malignant
      . Normal
  Instant prediction with confidence score

. Smart Reports: 
      . Auto-generated diagnostic reports
      . PDF download support (ReportLab)

. Healthcare System
      . Doctor discovery (verified profiles)
      . Appointment booking & management
      . Role-based dashboards (Doctor / Patient)

. Medical Records
      . Centralized scan history
      . Access past reports anytime

. Reviews & Ratings
      . Patient feedback system for doctors
      . Improves trust and transparency

. Search & Bookmarking
      . Search for doctors and records
      . Bookmark important doctors and reports

. Lifestyle Recommendations
      . Personalized health suggestions based on:
         . BMI
         . Diet
         . Sleep
         . Habits
         . Medical history

# Tech Stack
     . Frontend: HTML5, CSS3, JavaScript
     . Backend: Django (Python)
     . Machine Learning: Scikit-Learn, NumPy
     . Image Processing: OpenCV
     . Database: Django ORM
     . Reports: ReportLab (PDF generation)

# Objective
To bridge the gap between AI-based medical image analysis and real-world healthcare systems, enabling faster, more accessible thyroid disease detection and patient management.
