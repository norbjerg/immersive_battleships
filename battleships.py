from enum import Enum
from typing import Literal
from ast import literal_eval

from shift_valves import Table
from port import Port

tableActive = False

if (tableActive):
    t = Table(Port) #Change port in port.py to match the port of arduino

AVAILABLE_SHIPS = {
    2: 1,
    3: 1,
    4: 1,
    5: 1,
}

class GuessReturn(Enum):
    hit = "hit"
    miss = "miss"
    dupe_guess = "dupe_guess"
    finished_game = "finished_game"

class Ship:
    def __init__(self, start_pos: tuple[int, int], end_pos: tuple[int, int]) -> None:
        startx, starty = start_pos
        endx, endy = end_pos

        if startx - endx != 0 and starty - endy != 0:
            raise ValueError("Invalid ship configuration")

        if startx - endx > 0:
            self.filled = {(startx + i, starty) for i in range((startx - endx) + 1)}
        elif startx - endx < 0:
            self.filled = {(startx - i, starty) for i in range((endx - startx) + 1)}
        elif starty - endy > 0:
            self.filled = {(startx, starty + i) for i in range((starty - endy) + 1)}
        elif starty - endy < 0:
            self.filled = {(startx, starty - i) for i in range((endy - starty) + 1)}
        else:
            raise ValueError("Invalid ship configuration")

        self.lives = len(self.filled)


class PlayerBoard:
    def __init__(self, player_num: Literal[1, 2]) -> None:
        """
        ships is given as a dict with the beginning position of the ship as key, and size as value
        """
        self.x = 12
        self.y = 7
        self.player_num = player_num
        self.ships = []
        self.dead_ships = []
        self.guesses: set[tuple[int, int]] = set()
        self.board: dict[tuple[int, int], Ship] = {}

    def add_ships(self, ships: list[Ship]):
        for ship in ships:
            self.ships.append(ship)

            for coord in ship.filled:
                self.board[coord] = ship  # will make references

    def make_guess(self, coord: tuple[int, int]) -> GuessReturn:
        """
        Let the other player make a guess on this board.

        The coord param should be in the coordinate system of the full air table (i.e. 12x14)
        """
        calibrated_coord = coord
        if self.player_num == 2:
            x, y = coord
            calibrated_coord = (x, y + self.y)

        if coord in self.guesses:
            return GuessReturn.dupe_guess

        self.guesses.add(coord)

        if self.board[coord] is not None:
            self.board[coord].lives -= 1
            if self.board[coord].lives == 0:
                self.dead_ships.append(self.board[coord])
                print("A ship has been sunk")

        if tableActive:
            t.burst(calibrated_coord)
        else:
            print(calibrated_coord)

        if len(self.dead_ships) == len(self.ships):
            return GuessReturn.finished_game

        if self.board[coord] is not None:
            return GuessReturn.hit

        return GuessReturn.miss


def main():
    p1_ships = [Ship((0,0),(0,1)), Ship((1,0),(1,2)), Ship((2,0),(2,3)), Ship((3,0),(3,4))]
    p2_ships = [Ship((0,0),(0,1)), Ship((1,0),(1,2)), Ship((2,0),(2,3)), Ship((3,0),(3,4))]
    p1_board = PlayerBoard(1)
    p1_board.add_ships(p1_ships)
    p2_board = PlayerBoard(2)
    p2_board.add_ships(p2_ships)
    current_board = p1_board
    while current_board.make_guess(eval(input("Make a guess: "))) != GuessReturn.finished_game:
        if current_board != p1_board:
            current_board = p1_board
        else:
            current_board = p2_board


if __name__ == "__main__":
    main()
