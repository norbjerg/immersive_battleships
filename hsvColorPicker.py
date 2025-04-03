import cv2

def hsv_picker(image_path):
    img = cv2.imread(image_path)
    hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    def on_click(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            bgr = img[y, x]
            hsv = hsv_img[y, x]
            print(f"Clicked ({x},{y})")
            print(f"   BGR: {bgr}")
            print(f"   HSV: {hsv}")

    cv2.imshow("Click to sample color", img)
    cv2.setMouseCallback("Click to sample color", on_click)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

hsv_picker("images/colorscale.png")
