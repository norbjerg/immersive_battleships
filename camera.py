import cv2
import numpy as np
from cv2 import aruco
from sklearn.neighbors import KDTree

BOT_LEFT_ARUCO_ID = 0
TOP_RIGHT_ARUCO_ID = 1


class Camera:
    def __init__(self):
        self.cam = cv2.VideoCapture(0)

    def get_image(self) -> np.ndarray:
        result, image = self.cam.read()
        if result:
            return image
        raise RuntimeError("Could not capture image")

    def otsu_thresh(self):
        image = cv2.imread("Board_w_aruco.png")

        aruco_corners, ids, rejectedImgPoints = aruco.detectMarkers(
            image, aruco.getPredefinedDictionary(aruco.DICT_4X4_100)
        )

        ids = ids.reshape((ids.shape[0],))
        # four corners returned in their original order (which is clockwise starting with top left)
        ids_to_corners = dict(zip(ids, aruco_corners))

        grey = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        cv2.imwrite("DEBUG-grey.png", grey)

        gauss = cv2.GaussianBlur(grey, (5, 5), 0)
        cv2.imwrite("DEBUG-gauss.png", gauss)

        _, thresh = cv2.threshold(gauss, 200, 255, cv2.THRESH_BINARY)
        cv2.imwrite("DEBUG-thresh.png", thresh)
        cnts, _ = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        # cimg = cv2.drawContours(image, cnts,-1, (120,20,20),3)
        # cv2.imwrite("DEBUG-cont.png", cimg)

        centers = []

        for c in cnts:
            M = cv2.moments(c)
            cX = int(M["m10"] / M["m00"]) if M["m00"] != 0 else 0
            cY = int(M["m01"] / M["m00"]) if M["m00"] != 0 else 0
            if (
                cX > ids_to_corners[BOT_LEFT_ARUCO_ID][0][1][0]  # top right corner x
                and cY < ids_to_corners[BOT_LEFT_ARUCO_ID][0][1][1]  # top right corner y
                and cX < ids_to_corners[TOP_RIGHT_ARUCO_ID][0][3][0]  # bottom left corner x
                and cY > ids_to_corners[TOP_RIGHT_ARUCO_ID][0][3][1] + 2  # bottom left corner y
            ):
                centers.append((cX, cY))

        for center in centers:
            cv2.circle(image, center, 5, (20, 120, 20))

        cv2.imwrite("result.png", image)

        


cam = Camera()
cam.otsu_thresh()
