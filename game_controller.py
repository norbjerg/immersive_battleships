import time
from math import inf
from time import sleep

import cv2
import pyglet

import aruco_map
import helper_funcs
from battleships import Game, GuessReturn, Ship
from camera import Camera
from ui import GameStatus, Interface

SHIP_SIZE_MM = 15

COORD = tuple[int, int]


class GameController:
    def __init__(self, camera: Camera, dev: bool):
        self.camera = camera
        self.board_size = (14, 12)
        self.ships: list[Ship] | None = None
        self.game = None
        self.dev = dev

    def reset(self):
        self.ships = None
        self.game = None

    def try_initialize(self):
        detected_arucos = self.camera.get_ids_of_detected_arucos(
            self.camera.get_image()
        )
        if (
            aruco_map.PLAYER1_GUESS_CONFIRM not in detected_arucos
            and aruco_map.PLAYER2_GUESS_CONFIRM not in detected_arucos
        ):
            return
        self.ships = self.get_ships()
        if self.ships is None:
            return
        self.game = Game(board_size=self.board_size, ships=self.ships)

    def get_ships(self) -> list[Ship] | None:
        """
        Converts raw ship data from the camera into Ship objects.
        Each ship is a list of coordinates.
        """

        img = self.camera.get_image()
        detected_holes = self.camera.detect_holes(img, show_img=False)
        if not detect_holes:
            return None
        color_to_coords = self.camera.detect_colors(img, show_img=False)
        color_coords = [coord for coord_list in color_to_coords.values() for coord in coord_list]
        board_coords = detected_holes + color_to_coords
        if len(board_coords) != self.board_size[0] * self.board_size[1]:
            print("More holes than expected")
            return None

        board_coords_copy = board_coords.copy()
        board_coord_to_image_coord: dict[tuple[int, int], tuple[int, int]] = {}
        ship_len_to_board_coords: dict[int, list[tuple[int, int]]] = {}
        y_counter = 0
        while y_counter <= self.board_size[1] - 1:
            board_coords_copy.sort(key=lambda c: c[1])
            row = board_coords_copy[0 : self.board_size[0]]
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
            board_coords_copy = center_stack[BOARD_X_MAX + 1 :]
            y_counter += 1

        color_coord_to_hole_closest_distance: dict[COORD, tuple[COORD, float]] = {}

        color_coord_to_color = {
            coord: color
            for color, coords in color_to_coords.items()
            for coord in coords
        }

        for color_coord in color_coord_to_color:
            for board_coord, hole_coord in board_coord_to_hole.items():
                color_coord_to_hole_closest_distance.setdefault(
                    color_coord, ((0, 0), inf)
                )
                dist = helper_funcs.eucl_dist(color_coord, hole_coord)
                _, current_min = color_coord_to_hole_closest_distance[color_coord]
                if dist < current_min:
                    color_coord_to_hole_closest_distance[color_coord] = (
                        board_coord,
                        dist,
                    )

        color_to_board_coords = {}
        for color_coord, (
            board_coord,
            _,
        ) in color_coord_to_hole_closest_distance.items():
            color = color_coord_to_color[color_coord]
            color_to_board_coords.setdefault(color, [])
            color_to_board_coords[color].append(board_coord)

        ships = []

        coords = [
            coord for coords in color_to_board_coords.values() for coord in coords
        ]
        if len(set(coords)) != len(coords):
            print("Duplicate ship coords found", next(coord for coord in coords if coords.count(coord) > 1))
            return None

        for board_coords in color_to_board_coords.values():
            try:
                left, right = helper_funcs.split_coords(
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

        while self.game is None:
            self.try_initialize()
            interface.handle_game_status(GameStatus.await_ship_confirmation)
            last_time = self.handle_next_frame(last_time, interface)
            sleep(0.2)

        print([ship.filled for ship in self.ships])

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


if __name__ == "__main__":
    c = GameController(Camera(0), True)
    while True:
        img = c.camera.get_image()
        c.camera.detect_arucos(img.copy())
        g = c.get_guess(img, 1)
        if g:
            print(g)

        k = cv2.waitKey(5)
        if k == 27:
            break
