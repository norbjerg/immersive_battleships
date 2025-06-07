from camera import Camera
from game_controller import GameController
from hardware_variables import CameraNum
import argparse

def main(dev_mode=False):
    camera = Camera(CameraNum)
    game_controller = GameController(camera, dev_mode)
    game_controller.run()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-dev', action='store_true', help='Run in development mode')
    args = parser.parse_args()

    main(dev_mode=args.dev)
