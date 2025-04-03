import unittest
from battleships import *

class TestGame(unittest.TestCase):
    def test_switch_turn(self):
        game = Game((10,10),[])
        self.assertEqual(game.current_board.player_num, 2)
        game.switch_turn()
        self.assertEqual(game.current_board.player_num, 1)

    def test_current_turn(self):
        game = Game((10,10),[])
        self.assertEqual(game.current_board.player_num, 2)
        self.assertEqual(game.current_player(), 1)
        game.switch_turn()
        self.assertEqual(game.current_board.player_num, 1)
        self.assertEqual(game.current_player(), 2)

    def test_make_guess(self):
        game = Game((10,10),[Ship([(8,9), (9,9)], 2)])
        self.assertEqual(game.make_guess((1,1)), GuessReturn.out_of_bounds)
        self.assertEqual(game.current_player(), 1)
        self.assertEqual(game.make_guess((8, 8)), GuessReturn.miss)
        self.assertEqual(game.current_player(), 2)
        game.switch_turn()
        self.assertEqual(game.make_guess((8, 9)), GuessReturn.hit)
        self.assertEqual(game.current_player(), 2)
        game.switch_turn()
        self.assertEqual(game.make_guess((8, 9)), GuessReturn.dupe_guess)
        self.assertEqual(game.current_player(), 1)
        self.assertEqual(game.make_guess((9, 9)), GuessReturn.finished_game)




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

class TestPlayerBoard(unittest.TestCase):
    def test_add_ship(self):
        board = PlayerBoard((0, 10), (0, 10), [Ship([(0,0),(0,1),(0,2)], 1)], 1)
        expected_coords = [(0, 0), (0, 1), (0, 2)]
        for coord in expected_coords:
            self.assertIn(coord, board.board, f"Coordinate {coord} not found in board after initialization")

        with self.assertRaises(ValueError) as context:
            board.add_ships([Ship([(0,10), (0,11)], 1)])

        self.assertIn("Ship is out of bounds", str(context.exception))

    def test_in_bounds(self):
        board = PlayerBoard((0, 10), (0, 10), [Ship([(0,0),(0,1),(0,2)], 1)], 1)
        self.assertTrue(board.in_bounds((5,5)))
        self.assertTrue(board.in_bounds((10,0)))
        self.assertTrue(board.in_bounds((0,10)))
        self.assertTrue(board.in_bounds((10,10)))

        self.assertFalse(board.in_bounds((11,10)))
        self.assertFalse(board.in_bounds((10,11)))
        self.assertFalse(board.in_bounds((-1,0)))
        self.assertFalse(board.in_bounds((0,-1)))

    def test_make_guess(self):
        board = PlayerBoard((0, 10), (0, 10), [Ship([(0,0),(0,1)], 1)], 1)
        self.assertEqual(board.make_guess((0,1)), GuessReturn.hit)
        self.assertEqual(board.make_guess((0,1)), GuessReturn.dupe_guess)
        self.assertEqual(board.make_guess((-1,0)), GuessReturn.out_of_bounds)
        self.assertEqual(board.make_guess((0,10)), GuessReturn.miss)
        self.assertEqual(board.make_guess((0,0)), GuessReturn.finished_game)

class TestShip(unittest.TestCase):
    def test_vertical_ship(self):
        ship1 = Ship([(0,0),(0,1),(0,2)], 1)
        self.assertEqual(ship1.filled, {(0,0),(0,1),(0,2)}, "The ship is filled improperly (startY < endY)")
        ship2 = Ship([(0,2),(0,1),(0,0)], 1)
        self.assertEqual(ship2.filled, {(0,0),(0,1),(0,2)}, "The ship is filled improperly (startY > endY)")

    def test_horizontal_ship(self):
        ship1 = Ship([(0,0),(1,0),(2,0)], 1)
        self.assertEqual(ship1.filled, {(0,0),(1,0),(2,0)}, "The ship is filled improperly (startX < endX)")
        ship2 = Ship([(2,0),(1,0),(0,0)], 1)
        self.assertEqual(ship2.filled, {(0,0),(1,0),(2,0)}, "The ship is filled improperly (startX > endX)")

    def test_diagonal_ship(self):
        with self.assertRaises(ValueError):
            Ship([(0,0),(1,1),(2,2)], 1)

        with self.assertRaises(ValueError):
            Ship([(2,2),(1,1),(0,0)], 1)

    def test_1x1_ship(self):
        with self.assertRaises(ValueError):
            Ship([(0,0)], 1)

    def test_inproper_ship(self):
        with self.assertRaises(ValueError):
            Ship([(5,0),(0,5),(5,5)], 1)

        with self.assertRaises(ValueError):
            Ship([(0,5),(5,0),(5,5)], 1)





if __name__ == '__main__':
    unittest.main()
