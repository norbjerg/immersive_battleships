from ast import literal_eval
from enum import Enum
from typing import Literal

from port import Port
from shift_valves import Table

tableActive = False

if tableActive:
    t = Table(Port)

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
    """
    start_pos is the board coordinate of where one end of the ship is

    end_pos is the board coordinate of where the other end of the ship is

    player signifies which player the ship belongs to
    """

    def __init__(self, sections: list[tuple[int, int]], player: int) -> None:
        if not sections or len(sections) <= 1:
            raise ValueError("Ship must have at least two sections")
        self.player = player

        xs = [x for x, y in sections]
        ys = [y for x, y in sections]

        if all(x == xs[0] for x in xs):
            sorted_ys = sorted(ys)
            expected = list(range(sorted_ys[0], sorted_ys[0] + len(sections)))
            if sorted_ys != expected:
                raise ValueError(
                    f"Invalid vertical ship: got {sorted_ys}, expected {expected}"
                )
        elif all(y == ys[0] for y in ys):
            sorted_xs = sorted(xs)
            expected = list(range(sorted_xs[0], sorted_xs[0] + len(sections)))
            if sorted_xs != expected:
                raise ValueError(
                    f"Invalid vertical ship: got {sorted_xs}, expected {expected}"
                )
        else:
            raise ValueError("Ship sections must be in a straight line")

        self.filled = set(sections)
        self.lives = len(self.filled)


class Game:
    """
    board_size is given as the dimensions of the board being played

    ships are given as a list of Ship objects
    """

    def __init__(self, board_size: tuple[int, int], ships: list[Ship]) -> None:
        self.width, self.height = board_size
        self.p1_board = PlayerBoard(
            (0, self.width // 2 - 1),
            (0, self.height - 1),
            [ship for ship in ships if ship.player == 1],
            1,
        )
        self.p2_board = PlayerBoard(
            (self.width // 2, self.width - 1),
            (0, self.height - 1),
            [ship for ship in ships if ship.player == 2],
            2,
        )
        self.alternate = self.alternator()
        self.switch_turn()
        print(self.width)
        print(self.height)
        print(self.p1_board.x)
        print(self.p1_board.y)
        print(self.p2_board.x)
        print(self.p2_board.y)

    def alternator(self):
        while True:
            yield self.p2_board
            yield self.p1_board

    def switch_turn(self):
        self.current_board = next(self.alternate)

    def current_player(self) -> Literal[1, 2]:
        match self.current_board.player_num:
            case 1:
                return 2
            case 2:
                return 1
            case _:
                raise ValueError("Not a playernum")

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
    def __init__(
        self,
        width: tuple[int, int],
        height: tuple[int, int],
        ships: list[Ship],
        player_num: int,
    ) -> None:
        """
        ships are given as a list of Ship objects

        player_num identifies which player the board belongs to
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
        """
        Adds the ships to the board dictionary for easy lookup when making guesses
        """
        for ship in ships:
            for coord in ship.filled:
                if not self.in_bounds(coord):
                    raise ValueError(
                        f"Ship is out of bounds on player {self.player_num} board with coord:\n {ship.filled}"
                    )
                self.board[coord] = ship  # will make references

    def in_bounds(self, coord: tuple[int, int]) -> bool:
        """
        Checks if the given coord is in bounds of the players board
        """
        return self.x[0] <= coord[0] <= self.x[1] and self.y[0] <= coord[1] <= self.y[1]

    def make_guess(self, coord: tuple[int, int]) -> GuessReturn:
        """
        Let the other player make a guess on this board.

        The coord param should be in the coordinate system of the full air table (i.e. 14x12)
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
