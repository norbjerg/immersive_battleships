import time
from enum import Enum, auto
from random import randint

import pyglet
from pyglet import image, shapes, sprite, text


class GameStatus(Enum):
    await_ship_confirmation = auto()
    await_player1_guess = auto()
    await_player2_guess = auto()
    repeat_guess = auto()
    sunk_ship = auto()
    processing = auto()

    @classmethod
    def player_num_to_await(cls, player_num):
        if player_num == 1:
            return cls.await_player1_guess
        else:
            return cls.await_player2_guess


class InterfaceBoard:
    def __init__(
        self,
        corner: tuple[int, int],
        size: tuple[int, int],
        dim: tuple[int, int],
        player_num: int,
    ) -> None:
        x_size, y_size = size
        width, height = dim

        board_corner_x, board_corner_y = corner
        self.board = shapes.BorderedRectangle(
            board_corner_x, board_corner_y, width, height
        )
        self.xnumbers = [
            text.Label(
                str(x),
                board_corner_x + idx * 45 + 40,
                board_corner_y + 20,
                color=(0, 0, 0, 255),
            )
            for idx, x in enumerate("ABCDEFGHIJKL")
        ]
        self.xnumbers.append(
            text.Label(
                "x",
                board_corner_x + x_size * 45 + 40,
                board_corner_y + 20,
                color=(0, 0, 0, 255),
            )
        )
        self.ynumbers = [
            text.Label(
                str(y),
                board_corner_x + 20,
                board_corner_y + y * 45 + 60,
                color=(0, 0, 0, 255),
            )
            for y in range(y_size)
        ]
        self.ynumbers.append(
            text.Label(
                "y",
                board_corner_x + 20,
                board_corner_y + y_size * 45 + 40,
                color=(0, 0, 0, 255),
            )
        )
        self.board_coordinate_to_dot = {
            (x, y): shapes.Circle(
                board_corner_x + x * 45 + 40 + 5,
                board_corner_y + y * 45 + 60 + 5,
                2,
                color=(0, 0, 0, 255),
            )
            for x in range(x_size)
            for y in range(y_size)
        }

        self.player_num = text.Label(
            str(player_num),
            corner[0] + width // 2,
            100,
            color=(255, 255, 255, 255),
            font_size=40,
        )

        self.misses: list[shapes.ShapeBase] = []
        self.hits: list[text.DocumentLabel] = []

    def miss(self, coord: tuple[int, int]):
        """
        Draw miss on board.

        Note that coord is in coordinates the player gives as guess (12x7).
        """
        miss_node = self.board_coordinate_to_dot[coord]
        self.misses.append(
            shapes.Circle(miss_node.x, miss_node.y, 5, color=(20, 20, 255, 255))
        )

    def hit(self, coord: tuple[int, int]):
        """
        Draw hit on board.

        Note that coord is in coordinates the player gives as guess (12x7).
        """
        hit_node = self.board_coordinate_to_dot[coord]
        self.hits.append(
            text.Label(
                "X",
                hit_node.x - 1,
                hit_node.y + 5,
                anchor_x="center",
                anchor_y="center",
                font_size=20,
                color=(255, 20, 20, 255),
            )
        )

    def figures(self):
        return [
            self.board,
            self.player_num,
            *self.xnumbers,
            *self.ynumbers,
            *self.board_coordinate_to_dot.values(),
            *self.misses,
            *self.hits,
        ]

    def draw(self):
        for fig in self.figures():
            fig.draw()


class Interface(pyglet.window.Window):
    def __init__(self):
        super().__init__()
        self.set_size(1500, 600)
        self.key_handler = pyglet.window.key.KeyStateHandler()
        self.push_handlers(self.key_handler)

        x_size = 12
        y_size = 7
        width = x_size * 50
        height = y_size * 55

        self.board1 = InterfaceBoard(
            (
                self.width - width - 20,
                self.height - height - 20,
            ),
            (x_size, y_size),
            (width, height),
            1,
        )

        self.board2 = InterfaceBoard(
            (
                20,
                self.height - height - 20,
            ),
            (x_size, y_size),
            (width, height),
            2,
        )

        self.status_text: text.DocumentLabel = text.Label(
            "",
            self.width // 2 - 500,
            100,
            width=1000,
            height=100,
            color=(220, 0, 0, 255),
            align="center",
            multiline=True,
        )

    def next_frame(self):
        self.dispatch_events()
        self.clear()
        self.board1.draw()
        self.board2.draw()
        self.status_text.draw()
        self.flip()

    def hit(self, player_num: int, coord: tuple[int, int]):
        # coordinates are flipped because for the player it is flipped to the airtable
        # when making guess on board2, we need to offset it, because given are full airtable coords
        if player_num == 1:
            self.board2.hit((coord[1], coord[0] - 7))
        else:
            self.board1.hit((coord[1], coord[0]))

    def miss(self, player_num: int, coord: tuple[int, int]):
        if player_num == 1:
            self.board2.miss((coord[1], coord[0] - 7))
        else:
            self.board1.miss((coord[1], coord[0]))

    def handle_game_status(self, status: GameStatus):
        match status:
            case GameStatus.await_player1_guess:
                self.status_text.text = "Awaiting guess from player 1"
            case GameStatus.await_player2_guess:
                self.status_text.text = "Awaiting guess from player 2"
            case GameStatus.repeat_guess:
                self.status_text.text = "Repeat guess, please guess again"
            case GameStatus.sunk_ship:
                self.status_text.text = "A ship has been sunk"
            case GameStatus.processing:
                self.status_text.text = "Processing..."
            case GameStatus.await_ship_confirmation:
                self.status_text.text = (
                    "Awaiting for players to be ready.\n"
                    "Both players must hold down fire button when ready."
                )


if __name__ == "__main__":
    i = Interface()
    last_time = time.perf_counter()
    filled = set()
    player_num = 1
    game_state = GameStatus.await_player1_guess
    idx = 0
    state_lst = list(GameStatus)
    while True:
        if i.key_handler[pyglet.window.key.ESCAPE]:
            break
        if i.key_handler[pyglet.window.key.N]:
            idx += 1
            if idx >= len(state_lst):
                idx = 0
            game_state = list(GameStatus)[idx]
        if i.key_handler[pyglet.window.key._1]:
            player_num = 1
        if i.key_handler[pyglet.window.key._2]:
            player_num = 2
        if i.key_handler[pyglet.window.key.M]:
            guess = (randint(0, 11), randint(0, 6))
            while guess in filled:
                guess = (randint(0, 11), randint(0, 6))
            i.miss(player_num, guess)
        if i.key_handler[pyglet.window.key.H]:
            guess = (randint(0, 11), randint(0, 6))
            while guess in filled:
                guess = (randint(0, 11), randint(0, 6))
            i.hit(player_num, guess)
        i.handle_game_status(game_state)
        elapsed_time = time.perf_counter() - last_time
        if elapsed_time > 1 / 60:
            last_time = time.perf_counter()
            i.next_frame()
