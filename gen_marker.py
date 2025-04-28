from cv2 import aruco
import cv2

for i in range(10,50):
    code = aruco.generateImageMarker(aruco.getPredefinedDictionary(aruco.DICT_4X4_100), i, 100, None, 1)
    cv2.imwrite(f"./arucos/id{i}.png", code)
