from camera import Camera
from hardware import camera_num
from game_controller import GameController
import argparse

def main(dev_mode=False):
    camera = Camera(camera_num) #Set camera number in hardware.py matching number corresponding to webcam
    game_controller = GameController(camera, dev_mode)
    game_controller.run()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-dev', action='store_true', help='Run in development mode')
    args = parser.parse_args()

    main(dev_mode=args.dev)
