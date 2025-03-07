import cv2
import numpy as np
from matplotlib import pyplot as plt

class Camera:
    def __init__(self):
        self.cam = cv2.VideoCapture(0)

    def get_image(self) -> np.ndarray:
        result, image = self.cam.read()
        if result:
            return image
        raise RunTimeError("Could not capture image")

    def otsu_thresh(self):
        image = cv2.imread("Board.png")
        grey = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        cv2.imwrite("DEBUG-grey.png", grey)

        _, thresh = cv2.threshold(grey, 180, 255, cv2.THRESH_BINARY)
        cv2.imwrite("DEBUG-thresh.png", thresh)

    def k_mean(self):



cam = Camera()
cam.otsu_thresh()
