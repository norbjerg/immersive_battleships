import cv2
import numpy as np
from sklearn.neighbors import KDTree
from sklearn.neighbors import NearestNeighbors


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

        gauss = cv2.GaussianBlur(grey,(5,5),0)
        cv2.imwrite("DEBUG-gauss.png", gauss)

        _, thresh = cv2.threshold(gauss, 200, 255, cv2.THRESH_BINARY)
        cv2.imwrite("DEBUG-thresh.png", thresh)
        cnts, _ = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        cimg = cv2.drawContours(image, cnts,-1, (120,20,20),3)
        cv2.imwrite("DEBUG-cont.png", cimg)

        centers = []

        for c in cnts:
            M = cv2.moments(c)
            cX = int(M["m10"] / M["m00"]) if M["m00"] != 0 else 0
            cY = int(M["m01"] / M["m00"]) if M["m00"] != 0 else 0
            
            centers.append((cX,cY))

        tree = KDTree(centers)

        refined_centers = set()

        for center in centers:
            for idx_arr in tree.query_radius([center], r=20):
                if len(idx_arr) > 3:
                    for idx in idx_arr:
                        refined_centers.add(centers[idx])

        for center in refined_centers:
            image = cv2.circle(image, center, 5, (20,120,20))

        cv2.imshow("lol",image)
        cv2.waitKey(0)


        




cam = Camera()
cam.otsu_thresh()
