from random import randint
import time
import pyglet
from pyglet import shapes, text


class Interface(pyglet.window.Window):
    def __init__(self):
        super().__init__()
        self.set_size(1500, 600)
        x_size = 12
        y_size = 7
        width = x_size * 50
        height = y_size * 55
        self.key_handler = pyglet.window.key.KeyStateHandler()
        self.push_handlers(self.key_handler)
        board_corner_x, board_corner_y = (
            self.width - width - 20,
            self.height - height - 20,
        )
        self.board = shapes.BorderedRectangle(board_corner_x, board_corner_y, width, height)
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
        self.misses: list[shapes.ShapeBase] = []
        self.hits: list[text.DocumentLabel] = []

    def next_frame(self):
        self.dispatch_events()
        self.clear()
        self.board.draw()
        for num in self.xnumbers:
            num.draw()
        for num in self.ynumbers:
            num.draw()
        for c in self.board_coordinate_to_dot.values():
            c.draw()
        for m in self.misses:
            m.draw()
        for h in self.hits:
            h.draw()
        self.flip()

    def miss(self, coord: tuple[int,int]):
        """
        Draw miss on board.
        
        Note that coord is in coordinates the player gives as guess (12x7).
        """
        miss_node = self.board_coordinate_to_dot[coord]
        self.misses.append(
            shapes.Circle(
                miss_node.x,
                miss_node.y,
                5,
                color=(20,20,255,255)
            )
        )

    def hit(self, coord: tuple[int,int]):
        """
        Draw hit on board.
        
        Note that coord is in coordinates the player gives as guess (12x7).
        """
        hit_node = self.board_coordinate_to_dot[coord]
        self.hits.append(
            text.Label(
                "X",
                hit_node.x-1,
                hit_node.y+5,
                anchor_x="center",
                anchor_y="center",
                font_size=20,
                color=(255,20,20,255)
            )
        )



i = Interface()
last_time = time.perf_counter()
filled = set()
while True:
    if i.key_handler[pyglet.window.key.ESCAPE]:
        break
    if i.key_handler[pyglet.window.key.M]:
        guess = (randint(0,11),randint(0,6))
        while guess in filled:
            guess = (randint(0,11),randint(0,6))
        i.miss(guess)
    if i.key_handler[pyglet.window.key.H]:
        guess = (randint(0,11),randint(0,6))
        while guess in filled:
            guess = (randint(0,11),randint(0,6))
        i.hit(guess)
    elapsed_time = time.perf_counter() - last_time
    if elapsed_time > 1/60:
        last_time = time.perf_counter()
        i.next_frame()
