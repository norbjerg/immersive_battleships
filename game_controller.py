import time
from time import sleep

import cv2
import pyglet

import aruco_map
from battleships import Game, GuessReturn, Ship
from camera import Camera
from ui import GameStatus, Interface


class GameController:
    def __init__(self, camera: Camera, dev: bool):
        self.camera = camera
        self.board_size = (14, 12)  # Get board size from camera here
        self.ships: list[Ship] = self.get_ships()  # Get ships from the camera her
        self.game = Game(board_size=self.board_size, ships=self.ships)
        self.dev = dev

    def get_ships(self) -> list[Ship]:
        """
        Converts raw ship data from the camera into Ship objects.
        Each ship is a list of coordinates.
        """
        camera_ships = [
            [(0, 0), (0, 1), (0, 2)],
            [(13, 0), (12, 0), (11, 0)],
        ]  # self.camera.read_ships() #Read ships from camera here
        ships: list[Ship] = []

        for sections in camera_ships:
            if not sections:
                continue

            # Determine player by position on board. Unsure if we should check x or y here.
            left_half = all(x < self.board_size[0] // 2 for x, _ in sections)
            right_half = all(x >= self.board_size[0] // 2 for x, _ in sections)

            if not (left_half or right_half):
                print(f"Skipping ship crossing center line: {sections}")
                continue  # Invalid: ship crosses boundary

            player = 1 if left_half else 2
            try:
                ship = Ship(sections, player)
                ships.append(ship)
            except ValueError as e:
                print(f"Skipping invalid ship: {e}")
                print(f"Found at: {sections}")

        return ships

    def get_guess(
        self, img: cv2.typing.MatLike | None = None
    ) -> tuple[int, int] | None:
        img = img if img is not None else self.camera.get_image()
        ids = self.camera.get_ids_of_detected_arucos(img)
        player_num = self.game.current_player()

        if player_num == 1:
            x_map = aruco_map.PLAYER1_HORIZONTAL_X_COORD_TO_ARUCO_ID
            y_map = aruco_map.PLAYER1_VERTICAL_Y_COORD_TO_ARUCO_ID
            confirm = aruco_map.PLAYER1_GUESS_CONFIRM
        else:
            x_map = aruco_map.PLAYER2_HORIZONTAL_X_COORD_TO_ARUCO_ID
            y_map = aruco_map.PLAYER2_VERTICAL_Y_COORD_TO_ARUCO_ID
            confirm = aruco_map.PLAYER2_GUESS_CONFIRM
        if confirm not in ids:
            return None

        x_range = range(min(x_map), max(x_map))
        y_range = range(min(y_map), max(y_map))

        xs = [id for id in ids if id in x_range]
        ys = [id for id in ids if id in y_range]

        if not xs or not ys:
            return None

        if len(xs) > 1 or len(ys) > 1:
            print("More than one guess coord id found: xs", xs, "ys", ys)
            return None

        if xs[0] not in x_map or ys[0] not in y_map:
            print("KeyError: xs0", xs[0], "ys0", ys[0])
            return None

        return x_map[xs[0]], y_map[ys[0]]

    def handle_next_frame(self, last_time: float, interface: Interface):
        if interface.key_handler[pyglet.window.key.ESCAPE]:
            exit(0)

        elapsed_time = time.perf_counter() - last_time
        if elapsed_time > 1 / 60:
            last_time = time.perf_counter()
            interface.next_frame()
        return last_time

    def run(self):
        """
        Main game loop.
        """
        interface = Interface()
        last_time = time.perf_counter()

        while True:
            print(f"Player {self.game.current_player()}'s turn")
            interface.handle_game_status(
                GameStatus.player_num_to_await(self.game.current_player())
            )
            if self.dev:
                try:
                    last_time = self.handle_next_frame(last_time, interface)
                    for i in range(20):
                        continue
                    raw_input = input("Enter your guess (x,y): ").strip()
                    x_str, y_str = raw_input.split(",")
                    guess = (int(x_str), int(y_str))
                except ValueError:
                    print(
                        "Invalid input format. Please enter coordinates like '3,5'.\n"
                    )
                    continue
                    if not guess:
                        continue
            if not self.dev:
                print("Not in dev mode")
                # Get guess from camera here
                guess = None
                while guess is None:
                    guess = self.get_guess()
                    last_time = self.handle_next_frame(last_time, interface)
                    sleep(0.2)

            current_player = self.game.current_player()
            interface.handle_game_status(GameStatus.processing)
            result = self.game.make_guess(guess)

            match result:
                case GuessReturn.hit:
                    interface.hit(current_player, guess)
                case GuessReturn.miss:
                    interface.miss(current_player, guess)
                case GuessReturn.dupe_guess:
                    interface.handle_game_status(GameStatus.repeat_guess)

            print(f"Guess at {guess}: {result.value}")

            if result == GuessReturn.finished_game:
                print(f"Game Over! Player {self.game.current_player()} wins! ")
                break
            print(result)
