import cv2
import imutils
import numpy as np
from cv2 import aruco, typing

BOT_LEFT_ARUCO_ID = 0
TOP_RIGHT_ARUCO_ID = 1
CORNER_ARUCO_SIZE_MM = 45
BOTTOM_ARUCO_TO_TOP_HORIZONTAL_MM = (
    347  # Note that these are the bottom left corner of the markers
)
BOTTOM_ARUCO_TO_TOP_VERTICAL_MM = 279  # and top right corner respectively
OFFSET = 60
REAL_ARUCO_CORNERS = np.array(
    [
        # bottom left aruco
        [0 + OFFSET, BOTTOM_ARUCO_TO_TOP_VERTICAL_MM - CORNER_ARUCO_SIZE_MM + OFFSET],  # topleft
        [CORNER_ARUCO_SIZE_MM + OFFSET, BOTTOM_ARUCO_TO_TOP_VERTICAL_MM - CORNER_ARUCO_SIZE_MM + OFFSET],  # topright
        [CORNER_ARUCO_SIZE_MM + OFFSET, BOTTOM_ARUCO_TO_TOP_VERTICAL_MM + OFFSET],  # botright
        [0 + OFFSET, BOTTOM_ARUCO_TO_TOP_VERTICAL_MM + OFFSET],  # botleft
        # top right aruco
        [BOTTOM_ARUCO_TO_TOP_HORIZONTAL_MM - CORNER_ARUCO_SIZE_MM + OFFSET, 0 + OFFSET],  # topleft
        [BOTTOM_ARUCO_TO_TOP_HORIZONTAL_MM + OFFSET, 0 + OFFSET],  # topright
        [BOTTOM_ARUCO_TO_TOP_HORIZONTAL_MM + OFFSET, CORNER_ARUCO_SIZE_MM + OFFSET],  # botright
        [BOTTOM_ARUCO_TO_TOP_HORIZONTAL_MM - CORNER_ARUCO_SIZE_MM + OFFSET, CORNER_ARUCO_SIZE_MM + OFFSET],  # botleft
    ],
    dtype=np.float32
)
CORNER_ORIGIN_DISTANCE_MM = 10
HOLE_COUNT = 168
HOLE_DISTANCE_MM = 24
BOARD_X_MIN = 0
BOARD_Y_MIN = 0
BOARD_X_MAX = 13
BOARD_Y_MAX = 11
CLOSENESS_THRESHOLD = 2
BOUND_FEATHER = 10
SHIP_COLOR_TO_LEN = {
    "magenta": 2,
    "green": 3,
    "red": 4,
    "blue": 5,
}
COLOR_TO_BGR = {
    "blue": (255, 20, 20),
    "magenta": (236, 0, 252),
    "green": (20, 255, 20),
    "red": (20, 20, 255),
}


def img_show(img, title="lol"):
    cv2.imshow(title, img)
    cv2.waitKey(0)


class Camera:
    def __init__(self, cam_num: int):
        self.cam = cv2.VideoCapture(cam_num, cv2.CAP_DSHOW)

    def get_image(self) -> np.ndarray:
        result, image = self.cam.read()
        if result:
            return image
        raise RuntimeError("Could not capture image")

    def detect_holes(self, image: typing.MatLike, show_img: bool = False) -> list[tuple[float, float]]:
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        params = cv2.SimpleBlobDetector.Params()
        params.filterByArea = True
        params.minArea = 10
        params.maxArea = 100

        params.filterByCircularity = True
        params.minCircularity = 0.9

        detector = cv2.SimpleBlobDetector.create(params)
        keypoints = detector.detect(image)

        positions = [kp.pt for kp in keypoints]
        if show_img:
            vis = cv2.drawKeypoints(image, keypoints, None, (0, 0, 255),
                                    cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
            cv2.imshow('Detected Holes', vis)
            # cv2.waitKey(0)
            # cv2.destroyAllWindows()

        return positions

    def detect_colors(self, img, show_img: bool = True):
        """
        Detect colors (blue, green, magenta, red) from given image.

        Returns the name of the color to a list of centers of the colors in image coordinates.
        """

        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        lower_blue = np.array([100, 90, 50])
        upper_blue = np.array([130, 255, 255])
        blue_mask = cv2.inRange(hsv, lower_blue, upper_blue)

        cnts_blue = imutils.grab_contours(
            cv2.findContours(blue_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        )

        lower_green = np.array([35, 90, 50])
        upper_green = np.array([85, 255, 255])
        green_mask = cv2.inRange(hsv, lower_green, upper_green)
        cnts_green = imutils.grab_contours(
            cv2.findContours(green_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        )

        lower_magenta = np.array([135, 90, 50])
        upper_magenta = np.array([175, 255, 255])
        magenta_mask = cv2.inRange(hsv, lower_magenta, upper_magenta)
        cnts_magenta = imutils.grab_contours(
            cv2.findContours(magenta_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        )

        lower_red1 = np.array([0, 220, 100])
        upper_red1 = np.array([10, 255, 255])
        red_mask = cv2.inRange(hsv, lower_red1, upper_red1)

        cnts_red = imutils.grab_contours(
            cv2.findContours(red_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        )

        color_to_centers: dict[str, list[tuple[int, int]]] = {}
        image = img
        for clr, contours in zip(
            ("blue", "green", "magenta", "red"),
            (cnts_blue, cnts_green, cnts_magenta, cnts_red),
        ):
            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area > 50:
                    M = cv2.moments(cnt)
                    cX = int(M["m10"] / M["m00"]) if M["m00"] != 0 else 0
                    cY = int(M["m01"] / M["m00"]) if M["m00"] != 0 else 0
                    color_to_centers.setdefault(clr, [])
                    color_to_centers[clr].append((cX, cY))
                    cv2.drawContours(image, [cnt], -1, COLOR_TO_BGR[clr], 3)
                    cv2.circle(image, (cX, cY), 2, (255, 255, 255), -1)
                    cv2.putText(
                        image,
                        clr[0],
                        (cX - 20, cY - 20),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (255, 255, 255),
                        2,
                    )
        if show_img:
            cv2.imshow("colors", image)
        else:
            cv2.imwrite("DEBUG-colors.png", image)
        return color_to_centers

    def get_ids_of_detected_arucos(self, img) -> list[int]:
        aruco_corners, ids, rejectedImgPoints = aruco.detectMarkers(
            img, aruco.getPredefinedDictionary(aruco.DICT_4X4_250)
        )
        if ids is None:
            return []
        ids = ids.reshape((ids.shape[0],))
        return [int(id) for id in ids]

    def detect_arucos(self, img):
        aruco_corners, ids, rejectedImgPoints = aruco.detectMarkers(
            img, aruco.getPredefinedDictionary(aruco.DICT_4X4_250)
        )
        if ids is None:
            cv2.imshow("aruco", img)
            return
        ids = ids.reshape((ids.shape[0],))
        ids_to_corners = dict(zip(ids, aruco_corners))

        for id, aruco_ in ids_to_corners.items():
            cv2.circle(
                img, (int(aruco_[0][0][0]), int(aruco_[0][0][1])), 3, (255, 20, 20)
            )
            cv2.circle(
                img, (int(aruco_[0][1][0]), int(aruco_[0][1][1])), 3, (255, 20, 20)
            )
            cv2.circle(
                img, (int(aruco_[0][2][0]), int(aruco_[0][2][1])), 3, (255, 20, 20)
            )
            cv2.circle(
                img, (int(aruco_[0][3][0]), int(aruco_[0][3][1])), 3, (255, 20, 20)
            )
            cv2.putText(
                img,
                str(id),
                (int(aruco_[0][0][0]), int(aruco_[0][0][1])),
                3,
                3,
                (255, 20, 20),
            )
        cv2.imshow("aruco", img)

if __name__ == "__main__":
    cam = Camera(1)
    col = False
    while True:
        # img = cam.get_image()
        #img = cv2.imread("../Airtable.png")
        # img = cv2.imread("DEBUG-skew.png")
        # img = cv2.imread("DEBUG-too-many-holes.png")
        img = cv2.imread("DEBUG-raw-hands.png")
        img_raw = img.copy()
        if not col:
            col_img = img.copy()
            color_to_coords = cam.detect_colors(img)
            
            cam.detect_holes(col_img, False)

        elif col:
            cam.detect_arucos(img.copy())
        k = cv2.waitKey(5)
        if k == 27:
            break
        if k == ord("s"):
            col = not col
        if k == ord("d"):
            cv2.imwrite("DEBUG-raw.png", img_raw)
