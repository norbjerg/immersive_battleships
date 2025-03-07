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
        raise RuntimeError("Could not capture image")

    def otsu_thresh(self):
        image = cv2.imread("Board.png")
        grey = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        cv2.imwrite("DEBUG-grey.png", grey)

        _, thresh = cv2.threshold(grey, 254, 255, cv2.THRESH_BINARY_INV|cv2.THRESH_OTSU)
        cv2.imwrite("DEBUG-thresh.png", thresh)
        cnts, _ = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        cimg = cv2.drawContours(image, cnts,-1, (120,20,20),3)
        cv2.imwrite("result.png", cimg)


cam = Camera()
cam.otsu_thresh()
