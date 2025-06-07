from datetime import datetime
import cv2
import imutils
import numpy as np
from cv2 import aruco, typing

COLOR_TO_BGR = {
    "blue": (255, 20, 20),
    "magenta": (236, 0, 252),
    "green": (20, 255, 20),
    "red": (20, 20, 255),
}

def img_show(img, title="debug"):
    """
    Shows an image.

    Returns nothing.
    
    Used for debugging.
    """
    cv2.imshow(title, img)
    cv2.waitKey(0)


class Camera:
    def __init__(self, cam_num: int):
        self.cam = cv2.VideoCapture(cam_num, cv2.CAP_DSHOW)

    def get_image(self) -> np.ndarray:
        """
        Captures an image from the connected camera.

        Returns the captured image.
        """
        result, image = self.cam.read()
        if result:
            return image
        raise RuntimeError("Could not capture image")

    def detect_holes(self, image: typing.MatLike, show_img: bool = False) -> list[tuple[float, float]]:
        """
        Detects circular holes on the given image.

        Returns a list of the found holes in image coordinates.
        """
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

        return positions

    def detect_colors(self, img, show_img: bool = True):
        """
        Detect colors (blue, green, magenta, red) from given image.

        Returns the name of the color to a list of centers of the colors in image coordinates.
        """

        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        lower_blue = np.array([100, 70, 50])
        upper_blue = np.array([140, 255, 255])
        blue_mask = cv2.inRange(hsv, lower_blue, upper_blue)

        cnts_blue = imutils.grab_contours(
            cv2.findContours(blue_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        )

        lower_green = np.array([35, 80, 50])
        upper_green = np.array([85, 255, 255])
        green_mask = cv2.inRange(hsv, lower_green, upper_green)
        cnts_green = imutils.grab_contours(
            cv2.findContours(green_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        )

        lower_magenta = np.array([145, 80, 50])
        upper_magenta = np.array([175, 255, 255])
        magenta_mask = cv2.inRange(hsv, lower_magenta, upper_magenta)
        cnts_magenta = imutils.grab_contours(
            cv2.findContours(magenta_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        )

        lower_red1 = np.array([0, 180, 100])
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
                if area > 50 and area < 400:
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
        """
        Detects aruco codes present in a given image.

        Returns a list of ids of the found arucos.
        """
        _, ids, _ = aruco.detectMarkers(
            img, aruco.getPredefinedDictionary(aruco.DICT_4X4_250)
        )
        if ids is None:
            return []
        ids = ids.reshape((ids.shape[0],))
        return [int(id) for id in ids]

    def detect_arucos(self, img):
        """
        Detects aruco markers present in a given image.

        Highlights the found markers with ids and shows the image. Returns nothing.

        Primarily used for debugging purposes.
        """
        aruco_corners, ids, _ = aruco.detectMarkers(
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

    def record(self, stop_event):
        """
        Records video from the connected camera.

        Returns nothing.
        
        Primarily used for capturing video for report purposes.
        """
        video_capture = cv2.VideoWriter(
            f'video{int(datetime.now().timestamp())}.avi',
            cv2.VideoWriter.fourcc(*'MJPG'),
            24,
            (int(self.cam.get(3)),int(self.cam.get(4)))
        )

        while not stop_event.is_set():
            frame = self.get_image()

            video_capture.write(frame)
