import unittest
from battleships import *

#class TestGame(unittest.TestCase):

#class TestPlayerBoard(unittest.TestCase):


class TestShip(unittest.TestCase):
    def test_vertical_ship(self):
        ship1 = Ship((0,0),(0,2), 1)
        self.assertEqual(ship1.filled, {(0,0),(0,1),(0,2)}, "The ship is filled improperly (startY < endY)")
        ship2 = Ship((0,2),(0,0), 1)
        self.assertEqual(ship2.filled, {(0,0),(0,1),(0,2)}, "The ship is filled improperly (startY > endY)")

    def test_horizontal_ship(self):
        ship1 = Ship((0,0),(2,0), 1)
        self.assertEqual(ship1.filled, {(0,0),(1,0),(2,0)}, "The ship is filled improperly (startX < endX)")
        ship2 = Ship((2,0),(0,0), 1)
        self.assertEqual(ship2.filled, {(0,0),(1,0),(2,0)}, "The ship is filled improperly (startX > endX)")

    def test_diagonal_ship(self):
        with self.assertRaises(ValueError):
            Ship((0,0),(2,2), 1)

        with self.assertRaises(ValueError):
            Ship((2,2),(0,0), 1)

    def test_1x1_ship(self):
        with self.assertRaises(ValueError):
            Ship((0,0),(0,0), 1)

    def test_inproper_ship(self):
        with self.assertRaises(ValueError):
            Ship((5,0),(0,5), 1)

        with self.assertRaises(ValueError):
            Ship((0,5),(5,0), 1)





if __name__ == '__main__':
    unittest.main()
