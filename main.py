from camera import Camera
from game_controller import GameController

def main():
    camera = Camera(4) # Set camera number matching webcam
    game_controller = GameController(camera)
    game_controller.run()

if __name__ == "__main__":
    main()
