import cv2
import numpy as np
from skimage.feature import local_binary_pattern, graycomatrix, graycoprops, hog
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.models import Model

# 🔥 CNN INIT (GLOBAL)
base_model = MobileNetV2(
    weights='imagenet',
    include_top=False,
    input_shape=(224, 224, 3),
    pooling='avg'
)

cnn_extractor = Model(
    inputs=base_model.input,
    outputs=base_model.output
)

def extract_hybrid_features(img_path):

    img_cv = cv2.imread(img_path)
    if img_cv is None:
        return None

    img_cv = cv2.resize(img_cv, (224, 224))

    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    gray = clahe.apply(gray)

    # CNN
    img_rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
    img_batch = preprocess_input(np.expand_dims(img_rgb, axis=0))
    cnn_feats = cnn_extractor.predict(img_batch, verbose=0).flatten()

    # GLCM
    glcm = graycomatrix(gray, [1,2], [0,np.pi/4,np.pi/2], 256, symmetric=True, normed=True)
    glcm_feats = np.array([
        graycoprops(glcm, 'contrast').mean(),
        graycoprops(glcm, 'homogeneity').mean(),
        graycoprops(glcm, 'energy').mean(),
        graycoprops(glcm, 'correlation').mean()
    ], dtype=np.float32)

    # LBP
    lbp = local_binary_pattern(gray, 24, 3, method='uniform')
    lbp_hist, _ = np.histogram(lbp.ravel(), bins=26, range=(0,26))
    lbp_hist = lbp_hist.astype(np.float32)
    lbp_hist /= (lbp_hist.sum() + 1e-7)

    features = np.hstack([cnn_feats, lbp_hist, glcm_feats])

    # 🔥 FORCE FIX HERE (IMPORTANT)
    return features[:1310].astype(np.float32)

