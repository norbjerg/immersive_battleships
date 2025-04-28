import cv2
import imutils
import numpy as np
from cv2 import aruco, typing

BOT_LEFT_ARUCO_ID = 0
TOP_RIGHT_ARUCO_ID = 1
CORNER_ARUCO_SIZE_MM = 45
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
    def __init__(self):
        self.cam = cv2.VideoCapture(1)

    def get_image(self) -> np.ndarray:
        result, image = self.cam.read()
        if result:
            return image
        raise RuntimeError("Could not capture image")

    def otsu_thresh(self, image: typing.MatLike, show_img: bool = False):
        ids_to_corners = self.get_ids_to_corners_aruco(image, show_img)

        grey = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        if not show_img:
            cv2.imwrite("DEBUG-grey.png", grey)

        gauss = cv2.GaussianBlur(grey, (5, 5), 0)
        if not show_img:
            cv2.imwrite("DEBUG-gauss.png", gauss)

        thresh = cv2.adaptiveThreshold(
            gauss, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 131, 15
        )
        if not show_img:
            cv2.imwrite("DEBUG-thresh.png", thresh)
        cnts, _ = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        cnt_img = image.copy()
        cv2.drawContours(cnt_img, cnts, -1, (0, 255, 0), 3)
        if not show_img:
            cv2.imwrite("DEBUG-cont.png", cnt_img)

        centers = []

        raw_centers = image.copy()

        # Remove centers outside of the corners of the board
        for c in cnts:
            M = cv2.moments(c)
            cX = int(M["m10"] / M["m00"]) if M["m00"] != 0 else 0
            cY = int(M["m01"] / M["m00"]) if M["m00"] != 0 else 0
            cv2.circle(raw_centers, (cX, cY), 5, (20, 120, 20), 3)
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

        filter_corner = image.copy()
        for center in centers:
            cv2.circle(filter_corner, center, 5, (20, 120, 20), 3)
        cv2.imwrite("DEBUG-filter_corner.png", filter_corner)
        cv2.imwrite("DEBUG-raw_centers.png", raw_centers)

        # Add ships from colors
        color_centers = self.detect_colors(image, show_img=False)

        filtered_color_centers: dict[str, list[tuple[int, int]]] = {}
        center_to_color: dict[tuple[int, int], str] = {}

        # Filter out colors outside of the board
        for clr, cnt_lst in color_centers.items():
            for cX, cY in cnt_lst:
                if (
                    cX
                    > ids_to_corners[BOT_LEFT_ARUCO_ID][0][1][0]  # top right corner x
                    and cY
                    < ids_to_corners[BOT_LEFT_ARUCO_ID][0][1][1]  # top right corner y
                    and cX
                    < ids_to_corners[TOP_RIGHT_ARUCO_ID][0][3][0]
                    - 2  # bottom left corner x
                    and cY
                    > ids_to_corners[TOP_RIGHT_ARUCO_ID][0][3][1]
                    + 2  # bottom left corner y
                ):
                    filtered_color_centers.setdefault(clr, [])
                    filtered_color_centers[clr].append((cX, cY))
                    centers.append((cX, cY))
                    center_to_color[(cX, cY)] = clr

        # Remove centers too close to each other
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
            try:
                centers.pop(centers.index(c))
            except:
                pass

        close_center = image.copy()
        for center in centers:
            cv2.circle(close_center, center, 5, (20, 120, 20), 3)
        if not show_img:
            cv2.imwrite("DEBUG-close_center.png", close_center)

        # Remove black areas around ships
        color_to_bound: dict[str, tuple[int, int, int, int]] = {}
        for clr, center_lst in filtered_color_centers.items():
            min_x, max_x, min_y, max_y = (
                center_lst[0][0] - BOUND_FEATHER,
                center_lst[0][1] + BOUND_FEATHER,
                center_lst[0][0] - BOUND_FEATHER,
                center_lst[0][1] + BOUND_FEATHER,
            )
            for cX, cY in center_lst[1:]:
                if cX - BOUND_FEATHER < min_x:
                    min_x = cX - BOUND_FEATHER
                if cX + BOUND_FEATHER > max_x:
                    max_x = cX + BOUND_FEATHER
                if cY - BOUND_FEATHER < min_y:
                    min_y = cY - BOUND_FEATHER
                if cY + BOUND_FEATHER < max_y:
                    max_y = cY + BOUND_FEATHER

            color_to_bound[clr] = min_x, max_x, min_y, max_y

        remove_center = set()
        for cX, cY in centers:
            if (cX, cY) in center_to_color:
                continue
            for _, (min_x, max_x, min_y, max_y) in color_to_bound.items():
                if cX > min_x and cX < max_x and cY > min_y and cY < max_y:
                    remove_center.add((cX, cY))

        for c in remove_center:
            try:
                centers.pop(centers.index(c))
            except:
                pass

        for _, (min_x, max_x, min_y, max_y) in color_to_bound.items():
            cv2.rectangle(image, (min_x, min_y), (max_x, max_y), (255, 255, 20), 5)

        center_stack = centers.copy()

        board_coord_to_image_coord: dict[tuple[int, int], tuple[int, int]] = {}
        ship_len_to_board_coords: dict[int, list[tuple[int, int]]] = {}

        y_counter = 0
        while y_counter <= BOARD_Y_MAX:
            center_stack.sort(key=lambda c: c[1])
            row = center_stack[BOARD_X_MIN : BOARD_X_MAX + 1]
            row.sort(key=lambda c: c[0])
            for i, c in enumerate(row):
                board_coord_to_image_coord[(BOARD_X_MAX - i, y_counter)] = c
                if center_to_color.get(c):
                    ship_len_to_board_coords.setdefault(
                        SHIP_COLOR_TO_LEN[center_to_color[c]], []
                    )
                    ship_len_to_board_coords[
                        SHIP_COLOR_TO_LEN[center_to_color[c]]
                    ].append(
                        (
                            BOARD_X_MAX - i,
                            y_counter,
                        )
                    )
            center_stack = center_stack[BOARD_X_MAX + 1 :]
            y_counter += 1

        for center in centers:
            cv2.circle(image, center, 5, (20, 120, 20), 3)
        if not show_img:
            cv2.imwrite("DEBUG-centers.png", image)
        else:
            cv2.imshow("centers", image)

        return ship_len_to_board_coords

    def detect_colors(self, img, show_img: bool = True):
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        lower_blue = np.array([100, 100, 50])
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

        lower_magenta = np.array([140, 100, 50])
        upper_magenta = np.array([170, 255, 255])
        magenta_mask = cv2.inRange(hsv, lower_magenta, upper_magenta)
        cnts_magenta = imutils.grab_contours(
            cv2.findContours(magenta_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
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

        color_to_centers: dict[str, list[tuple[int, int]]] = {}
        image = img.copy()
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
                    cv2.circle(image, (cX, cY), 7, (255, 255, 255), -1)
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

    def get_ids_to_corners_aruco(self, image, show_img: bool = True):
        aruco_corners, ids, rejectedImgPoints = aruco.detectMarkers(
            image, aruco.getPredefinedDictionary(aruco.DICT_4X4_100)
        )

        if ids is None:
            if show_img:
                cv2.imshow("centers", image)
                return {}
            print("No arucos were found")
            exit()

        ids = ids.reshape((ids.shape[0],))
        # four corners returned in their original order (which is clockwise starting with top left)
        ids_to_corners = dict(zip(ids, aruco_corners))
        if (
            BOT_LEFT_ARUCO_ID not in ids_to_corners
            or TOP_RIGHT_ARUCO_ID not in ids_to_corners
        ):
            if show_img:
                cv2.imshow("centers", image)
                return {}
            print(
                "Arucos for corners:",
                BOT_LEFT_ARUCO_ID,
                TOP_RIGHT_ARUCO_ID,
                "were not found",
            )
            exit()
        return ids_to_corners

    def detect_holes_from_aruco(self, image, show_img: bool = True):
        ids_to_corners = self.get_ids_to_corners_aruco(image, show_img)
        if not ids_to_corners:
            return
        pixel_side_len = 0

        for corners in ids_to_corners.values():
            side_len_sum = 0
            for idx, (cornerX, cornerY) in enumerate(corners[0][1:]):
                prev_cornerX, prev_cornerY = corners[0][idx]
                side_len_sum += (
                    (prev_cornerX - cornerX) ** 2 + (prev_cornerY - cornerY) ** 2
                ) ** 0.5

            pixel_side_len += side_len_sum / 3
        pixel_side_len = int(pixel_side_len // 2)

        mm_per_px = CORNER_ARUCO_SIZE_MM / pixel_side_len
        px_per_mm = pixel_side_len / CORNER_ARUCO_SIZE_MM

        id1_corners: list[list[int]] = list(ids_to_corners[TOP_RIGHT_ARUCO_ID][0])
        id1_corners.sort(key=lambda c: c[1], reverse=True)
        id1_corners = id1_corners[:2]
        id1_corners.sort(key=lambda c: c[0])
        bottom_left_corner_id1 = id1_corners[0]
        
        origin = (int(bottom_left_corner_id1[0]-7.5*px_per_mm), int(bottom_left_corner_id1[1]+7.5*px_per_mm))
        cv2.circle(image,origin,5,(20,20,255))

        for i in range(BOARD_X_MAX+1):
            for j in range(BOARD_Y_MAX+1):
                if i+j==0:
                    continue
                cv2.circle(image,(origin[0]-22*i,origin[1]+22*j),5,(20,20,255))
                

        img_show(image)

cam = Camera()
# print(cam.otsu_thresh(cv2.imread("images/board_w_green.png")))
# print(cam.otsu_thresh(cam.get_image()))

# cam.detect_holes_from_aruco(cv2.imread("images/board_clear2.png"))

while True:
    img = cam.get_image()
    cam.detect_holes_from_aruco(img.copy(), show_img=True)
    k = cv2.waitKey(5)
    if k == 27:
        break
    if k == ord("d"):
        cv2.imwrite("DEBUG-raw.png", img)
# while True:
#     print(cam.otsu_thresh(cv2.imread("images/board_w_magenta.png"), show_img=False))
#     break
#     img = cam.get_image()
#     cam.otsu_thresh(img.copy(), show_img=True)
#     k = cv2.waitKey(5)
#     if k == 27:
#         break
#     if k == ord("d"):
#         cv2.imwrite("DEBUG-raw.png", img)

# i = 0
# while True:
#     l = cam.detect_colors(cv2.imread("./images/2_smaller_greens.jpg"))
#     if i == 0:
#         print(l)
#         i += 1
#     # cam.detect_colors(cam.get_image())

#     k = cv2.waitKey(5)
#     if k == 27:
#         break
