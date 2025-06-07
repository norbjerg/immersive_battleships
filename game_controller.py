import time
from time import sleep
import cv2
import pyglet

import aruco_map
from battleships import Game, GuessReturn, Ship
from camera import Camera
from ui import GameStatus, Interface
import threading

SHIP_SIZE_MM = 15

COORD = tuple[int, int]


class GameController:
    def __init__(self, camera: Camera, dev: bool):
        self.camera = camera
        self.board_size = (14, 12)
        self.ships: list[Ship] | None = None
        self.game = None
        self.dev = dev
        self.stop_event = threading.Event()

    def reset(self):
        """
        Resets the game.
        """
        self.ships = None
        self.game = None

    def split_coords(self, board_x_len: int, points: list[tuple[int, int]]):
        """
        Splits coordinates into board sides.

        Returns a list with coords split into left and right halves.

        x_coord is usually something like self.board_size[0]
        """
        left_half = [point for point in points if point[0] < board_x_len // 2]
        right_half = [point for point in points if point[0] >= board_x_len // 2]
        if len(left_half) != len(right_half):
            raise ValueError("More ship sections on one side")
        return ((left_half, 1), (right_half, 2))

    def try_initialize(self):
        """
        Tries to initialize the game.
        """
        if self.dev:
            self.ships = self.get_dev_ships()
            self.game = Game(board_size=self.board_size, ships=self.ships)


        detected_arucos = self.camera.get_ids_of_detected_arucos(
            self.camera.get_image()
        )
        pl1x = aruco_map.PLAYER1_VERTICAL_Y_COORD_TO_ARUCO_ID
        pl1y = aruco_map.PLAYER1_HORIZONTAL_X_COORD_TO_ARUCO_ID
        pl2x = aruco_map.PLAYER2_VERTICAL_Y_COORD_TO_ARUCO_ID
        pl2y = aruco_map.PLAYER2_HORIZONTAL_X_COORD_TO_ARUCO_ID

        zero_ids = {min(pl_dict.keys()) for pl_dict in (pl1x, pl1y, pl2x, pl2y)}
        detected_arucos_set = set(detected_arucos)
        if not zero_ids.issubset(detected_arucos_set):
            return
        self.ships = self.get_ships()
        if self.ships is None:
            return
        self.game = Game(board_size=self.board_size, ships=self.ships)

    def get_dev_ships(self) -> list[Ship]:
        """
        Provides the list of ships for development mode.

        Returns a list of ships.
        """

        camera_ships = [[(0,0),(0,1),(0,2)],[(13,0),(12,0),(11,0)]]
        ships: list[Ship] = []

        for sections in camera_ships:
            if not sections:
                continue

            # Determine player by position on board.
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

    def get_ships(self, image: cv2.typing.MatLike | None = None) -> list[Ship] | None:
        """
        Converts raw ship data from the camera into Ship objects.
        Each ship is a list of coordinates.

        Returns list of ships if creation was succesful. Else it returns None.
        """

        img = image if image is not None else self.camera.get_image()
        detected_holes = self.camera.detect_holes(img, show_img=False)
        if not detected_holes:
            return None
        color_to_coords = self.camera.detect_colors(img, show_img=False)
        coord_to_color = {
            coord: color
            for color, coord_lst in color_to_coords.items()
            for coord in coord_lst
        }
        color_coords = [
            coord for coord_list in color_to_coords.values() for coord in coord_list
        ]
        board_coords = [
            (int(detected_hole[0]), int(detected_hole[1]))
            for detected_hole in detected_holes
        ] + color_coords
        if len(board_coords) != self.board_size[0] * self.board_size[1]:
            print("More holes than expected (actual, expected, colors, holes)", len(board_coords), self.board_size[0] * self.board_size[1], len(color_coords), len(detected_holes))
            return None

        board_coords_copy = board_coords.copy()
        image_coord_to_board_coord: dict[tuple[int, int], tuple[int, int]] = {}
        y_counter = 0
        while y_counter <= self.board_size[1] - 1:
            board_coords_copy.sort(key=lambda c: c[1])
            row = board_coords_copy[0 : self.board_size[0]]
            row.sort(key=lambda c: c[0])
            for i, c in enumerate(row):
                image_coord_to_board_coord[c] = (
                    (self.board_size[0] - 1) - i,
                    y_counter,
                )
            board_coords_copy = board_coords_copy[self.board_size[0] :]
            y_counter += 1

        color_to_board_coords: dict[str, list[tuple[int,int]]] = {}
        for color_coord in color_coords:
            color_to_board_coords.setdefault(coord_to_color[color_coord], [])
            color_to_board_coords[coord_to_color[color_coord]].append(
                image_coord_to_board_coord[color_coord]
            )
        print(color_to_board_coords)

        ships = []

        coords = [
            coord for coords in color_to_board_coords.values() for coord in coords
        ]
        if len(set(coords)) != len(coords):
            print(
                "Duplicate ship coords found",
                next(coord for coord in coords if coords.count(coord) > 1),
            )
            return None

        for board_coords in color_to_board_coords.values():
            try:
                left, right = self.split_coords(
                    self.board_size[0], board_coords
                )
            except ValueError as e:
                print(f"Invalid ship formation: {e}")
                return None

            for side in (left, right):
                try:
                    ship = Ship(*side)
                    ships.append(ship)
                except ValueError as e:
                    print(f"Skipping invalid ship: {e}")
                    print(f"Found at: {side}")
                    return None

        return ships

    def get_guess(
        self, img: cv2.typing.MatLike | None = None, player_num: int | None = None
    ) -> tuple[int, int] | None:
        """
        Tries to read the guess from the camera

        Returns guess if present. Else it returns None
        """
        img = img if img is not None else self.camera.get_image()
        ids = self.camera.get_ids_of_detected_arucos(img)
        if not player_num:
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

        x_range = range(min(x_map), max(x_map) + 1)
        y_range = range(min(y_map), max(y_map) + 1)

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

        return y_map[ys[0]], x_map[xs[0]]

    def handle_next_frame(self, last_time: float, interface: Interface):
        """
        Generates the next frame for the UI.

        Returns the last time the UI was updated.
        """
        if interface.key_handler[pyglet.window.key.ESCAPE]:
            self.stop_event.set()
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

        if not self.dev:
            recording_thread = threading.Thread(target=self.camera.record, args=(self.stop_event,))
            recording_thread.start()
            
        while self.game is None:
            self.try_initialize()
            interface.handle_game_status(GameStatus.await_ship_confirmation)
            last_time = self.handle_next_frame(last_time, interface)
            sleep(0.2)

        print([ship.filled for ship in self.ships])
        dupe_guess = False
        while True:
            print(f"Player {self.game.current_player()}'s turn")
            if not dupe_guess:
                interface.handle_game_status(
                    GameStatus.player_num_to_await(self.game.current_player())
                )
            if self.dev:
                try:
                    last_time = self.handle_next_frame(last_time, interface)
                    sleep(0.2)
                    raw_input = input("Enter your guess (x,y): ").strip()
                    x_str, y_str = raw_input.split(",")
                    guess = (int(x_str), int(y_str))
                except ValueError:
                    print(
                        "Invalid input format. Please enter coordinates like '3,5'.\n"
                    )
                    continue
            if not self.dev:
                guess = None
                while guess is None:
                    guess = self.get_guess()
                    last_time = self.handle_next_frame(last_time, interface)
                    sleep(0.2)

            current_player = self.game.current_player()
            result = self.game.make_guess(guess)

            dupe_guess = False
            match result:
                case GuessReturn.hit:
                    interface.hit(current_player, guess)
                case GuessReturn.miss:
                    interface.miss(current_player, guess)
                case GuessReturn.dupe_guess:
                    interface.handle_game_status(GameStatus.repeat_guess)
                    dupe_guess = True

            print(f"Guess at {guess}: {result.value}")

            if result == GuessReturn.finished_game:
                print(f"Game Over! Player {self.game.current_player()} wins! ")
                break
            print(result)
        self.stop_event.set()
        exit(0)
