import pyglet
from pyglet import shapes, text


class Interface:
    def __init__(self) -> None:
        self.window = pyglet.window.Window()

    def main(self):
        width = 140 * 5
        height = 120 * 5
        board_corner_x, board_corner_y = (
            self.window.width - width - 20,
            self.window.height - height - 20,
        )
        board = shapes.BorderedRectangle(board_corner_x, board_corner_y, width, height)
        xnumbers = [
            text.Label(
                str(x),
                board_corner_x + x * 45 + 40,
                board_corner_y + 20,
                color=(0, 0, 0, 255),
            )
            for x in range(14)
        ]
        ynumbers = [
            text.Label(
                str(y),
                board_corner_x + 20,
                board_corner_y + y * 45 + 60,
                color=(0, 0, 0, 255),
            )
            for y in range(12)
        ]
        board_coordinate_to_dot = {
            (x, y): shapes.Circle(
                board_corner_x + x * 45 + 40,
                board_corner_y + y * 45 + 60,
                2,
                color=(0, 0, 0, 255),
            )
            for x in range(14)
            for y in range(12)
        }

        @self.window.event
        def on_draw():
            self.window.clear()
            board.draw()
            for num in xnumbers:
                num.draw()
            for num in ynumbers:
                num.draw()
            for c in board_coordinate_to_dot.values():
                c.draw()

        pyglet.app.run()


i = Interface()
i.main()
