import cv2
import imutils
import numpy as np
from cv2 import aruco

BOT_LEFT_ARUCO_ID = 0
TOP_RIGHT_ARUCO_ID = 1
BOARD_X_MIN = 0
BOARD_Y_MIN = 0
BOARD_X_MAX = 13
BOARD_Y_MAX = 11
CLOSENESS_THRESHOLD = 2


def show_img(img, title="lol"):
    cv2.imshow(title, img)
    cv2.waitKey(0)


class Camera:
    def __init__(self):
        self.cam = cv2.VideoCapture(4)

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

        thresh = cv2.adaptiveThreshold(
            gauss, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 131, 15
        )
        cv2.imwrite("DEBUG-thresh.png", thresh)
        cnts, _ = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

        centers = []

        for c in cnts:
            M = cv2.moments(c)
            cX = int(M["m10"] / M["m00"]) if M["m00"] != 0 else 0
            cY = int(M["m01"] / M["m00"]) if M["m00"] != 0 else 0
            if (
                cX > ids_to_corners[BOT_LEFT_ARUCO_ID][0][1][0]  # top right corner x
                and cY
                < ids_to_corners[BOT_LEFT_ARUCO_ID][0][1][1]  # top right corner y
                and cX
                < ids_to_corners[TOP_RIGHT_ARUCO_ID][0][3][0]
                - 2  # bottom left corner x
                and cY
                > ids_to_corners[TOP_RIGHT_ARUCO_ID][0][3][1]
                + 2  # bottom left corner y
            ):
                centers.append((cX, cY))

        remove_center = []
        checked = set()
        for idx0, (c0x, c0y) in enumerate(centers):
            for idx1, (c1x, c1y) in enumerate(centers):
                if idx0 == idx1:
                    continue
                if (idx1, idx0) in checked:
                    continue
                dist = ((c0x - c1x) ** 2 + (c0y - c1y) ** 2) ** 0.5
                if dist <= CLOSENESS_THRESHOLD:
                    remove_center.append(centers[idx0])
                checked.add((idx0, idx1))

        for c in remove_center:
            centers.pop(centers.index(c))

        center_stack = centers.copy()

        board_coord_to_image_coord: dict[tuple[int, int], tuple[int, int]] = {}

        y_counter = 0
        while y_counter <= BOARD_Y_MAX:
            center_stack.sort(key=lambda c: c[1])
            row = center_stack[BOARD_X_MIN : BOARD_X_MAX + 1]
            row.sort(key=lambda c: c[0])
            for i, c in enumerate(row):
                board_coord_to_image_coord[(BOARD_X_MAX - i, y_counter)] = c
            center_stack = center_stack[BOARD_X_MAX + 1 :]
            y_counter += 1

        for center in centers:
            cv2.circle(image, center, 5, (20, 120, 20))
        cv2.imwrite("DEBUG-centers.png", image)

    def detect_colors(self, img):
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        lower_blue = np.array([100, 100, 100])
        upper_blue = np.array([130, 255, 255])
        blue_mask = cv2.inRange(hsv, lower_blue, upper_blue)

        cnts_blue = imutils.grab_contours(
            cv2.findContours(blue_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        )

        lower_green = np.array([55, 100, 50])
        upper_green = np.array([85, 255, 255])
        green_mask = cv2.inRange(hsv, lower_green, upper_green)
        cnts_green = imutils.grab_contours(
            cv2.findContours(green_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        )

        lower_yellow = np.array([15, 100, 100])
        upper_yellow = np.array([35, 255, 255])
        yellow_mask = cv2.inRange(hsv, lower_yellow, upper_yellow)
        cnts_yellow = imutils.grab_contours(
            cv2.findContours(yellow_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        )

        lower_red1 = np.array([0, 100, 100])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([175, 100, 100])
        upper_red2 = np.array([179, 255, 255])
        red_mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
        red_mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
        red_mask = red_mask1 | red_mask2

        cnts_red = imutils.grab_contours(
            cv2.findContours(red_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        )

        for clr, contours in zip(
            ("blue", "green", "yellow", "red"),
            (cnts_blue, cnts_green, cnts_yellow, cnts_red),
        ):
            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area > 500:
                    cv2.drawContours(img, [cnt], -1, (0, 255, 0), 3)
                    M = cv2.moments(cnt)
                    cX = int(M["m10"] / M["m00"]) if M["m00"] != 0 else 0
                    cY = int(M["m01"] / M["m00"]) if M["m00"] != 0 else 0
                    cv2.circle(img, (cX, cY), 7, (255, 255, 255), -1)
                    cv2.putText(
                        img,
                        clr,
                        (cX - 20, cY - 20),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        2.5,
                        (255, 255, 255),
                        3,
                    )
        cv2.imshow("colors", img)


cam = Camera()
# cam.otsu_thresh()
while True:
    cam.detect_colors(cv2.imread("colorscale.png"))

    k = cv2.waitKey(5)
    if k == 27:
        break
