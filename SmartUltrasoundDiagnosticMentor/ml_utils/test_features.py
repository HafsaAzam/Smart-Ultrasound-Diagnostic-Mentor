# Using unittest (Standard Library)

import unittest
import numpy as np
from unittest.mock import MagicMock
from features import extract_hybrid_features

class TestFeatureExtraction(unittest.TestCase):
    def setUp(self):
        self.mock_model = MagicMock()
        self.mock_model.predict.return_value = np.zeros((1, 1280))
        self.dummy_img = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)

    def test_output_is_not_none(self):
        features = extract_hybrid_features(self.dummy_img, self.mock_model)
        self.assertIsNotNone(features)

    def test_output_type(self):
        features = extract_hybrid_features(self.dummy_img, self.mock_model)
        self.assertIsInstance(features, np.ndarray)

if __name__ == '__main__':
    unittest.main()


# Using pytest
import pytest
import numpy as np
import cv2
from unittest.mock import MagicMock
from features import extract_hybrid_features

# Fixture to create a fake CNN model
@pytest.fixture
def mock_cnn_model():
    model = MagicMock()
    # MobileNetV2 output is (1, 1280)
    model.predict.return_value = np.zeros((1, 1280))
    return model

# Fixture to create a dummy image
@pytest.fixture
def dummy_image():
    return np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)

def test_feature_vector_length(mock_cnn_model, dummy_image):
    features = extract_hybrid_features(dummy_image, mock_cnn_model)
    # Total = 1280 (CNN) + 26 (LBP) + 4 (GLCM) + [HOG features]
    # Calculate expected length based on your current hog parameters
    assert isinstance(features, np.ndarray)
    assert features.size > 1310


# import os
# from django.conf import settings

# path = os.path.join(settings.BASE_DIR, "ml_models", "my_clinical_model.pkl")
# model = joblib.load(path)