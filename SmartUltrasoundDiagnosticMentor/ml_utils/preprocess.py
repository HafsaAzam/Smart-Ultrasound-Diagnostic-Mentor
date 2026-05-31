import cv2

def preprocess(image):
    """
    Preprocessing step matching training pipeline
    """

    # Convert image to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    return gray