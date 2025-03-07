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
    out_of_bounds = "out_of_bounds"
    finished_game = "finished_game"

class Ship:
    def __init__(self, start_pos: tuple[int, int], end_pos: tuple[int, int], player: int) -> None:
        startx, starty = start_pos
        endx, endy = end_pos
        self.player = player

        if startx - endx != 0 and starty - endy != 0:
            raise ValueError("Invalid ship configuration")

        if startx - endx > 0:
            self.filled = {(startx - i, starty) for i in range((startx - endx) + 1)}
        elif startx - endx < 0:
            self.filled = {(startx + i, starty) for i in range((endx - startx) + 1)}
        elif starty - endy > 0:
            self.filled = {(startx, starty - i) for i in range((starty - endy) + 1)}
        elif starty - endy < 0:
            self.filled = {(startx, starty + i) for i in range((endy - starty) + 1)}
        else:
            raise ValueError("Invalid ship configuration")

        self.lives = len(self.filled)

class Game:
    def __init__(self, board_size: tuple[int, int], ships: list[Ship]) -> None:
        self.width, self.height = board_size
        self.p1_board = PlayerBoard((0,self.width//2-1),(0,self.height-1),[ship for ship in ships if ship.player == 1], 1)
        self.p2_board = PlayerBoard((self.width//2, self.width-1),(0,self.height-1),[ship for ship in ships if ship.player == 2], 2)
        self.alternate = self.alternator()
        self.switch_turn()

    def alternator(self):
        while True:
            yield self.p2_board
            yield self.p1_board

    def switch_turn(self):
        self.current_board = next(self.alternate)

    def current_player(self):
        match self.current_board.player_num:
            case 1:
                return 2
            case 2:
                return 1

    def make_guess(self, guess: tuple[int, int]) -> GuessReturn:
        game_state = self.current_board.make_guess(guess)
        match game_state:
            case GuessReturn.out_of_bounds:
                print(f"The guess was {guess}")
                return game_state
            case GuessReturn.dupe_guess:
                return game_state
            case GuessReturn.finished_game:
                return game_state
            case _:
                self.switch_turn()
                return game_state

class PlayerBoard:
    def __init__(self, width: tuple[int, int], height: tuple[int, int], ships: list[Ship], player_num: int) -> None:
        """
        ships is given as a dict with the beginning position of the ship as key, and size as value
        """
        self.x = width
        self.y = height
        self.player_num = player_num
        self.ships = ships
        self.dead_ships = []
        self.guesses: set[tuple[int, int]] = set()
        self.board: dict[tuple[int, int], Ship] = {}
        self.add_ships(ships)

    def add_ships(self, ships: list[Ship]):
        for ship in ships:
            for coord in ship.filled:
                self.board[coord] = ship  # will make references

    def in_bounds(self, coord: tuple[int, int]) -> bool:
        return (self.x[0] <= coord[0] <= self.x[1]
            and self.y[0] <= coord[1] <= self.y[1])

    def make_guess(self, coord: tuple[int, int]) -> GuessReturn:
        """
        Let the other player make a guess on this board.

        The coord param should be in the coordinate system of the full air table (i.e. 12x14)
        """
        if coord in self.guesses:
            return GuessReturn.dupe_guess

        if not self.in_bounds(coord):
            return GuessReturn.out_of_bounds

        self.guesses.add(coord)

        if tableActive:
            t.burst(coord)
        else:
            print(coord)

        if self.board.get(coord) is not None:
            self.board[coord].lives -= 1
            if self.board[coord].lives == 0:
                self.dead_ships.append(self.board[coord])
                print("A ship has been sunk")

        if len(self.dead_ships) == len(self.ships):
            return GuessReturn.finished_game

        if self.board.get(coord) is not None:
            return GuessReturn.hit

        return GuessReturn.miss


def main():
    if tableActive:
        t.clear()

    game = Game((14, 12), [Ship((0,0),(4,0),1), Ship((13,12),(13,10),2)])
    while True:
        result = game.make_guess(eval(input(f"Player {game.current_player()} make a guess\n")))
        print(result)
        if result == GuessReturn.finished_game:
            print(f"PLAYER {game.current_player()} WON")
            return

if __name__ == "__main__":
    main()
