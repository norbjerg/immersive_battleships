from camera import Camera
from battleships import Game, Ship, GuessReturn

class GameController:
    def __init__(self, camera: Camera):
        self.camera = camera
        self.board_size = (14,12)# Get board size from camera here
        self.ships: list[Ship] = [Ship([(0,0),(0,1),(0,2)], 1), Ship([(0,11),(0,12),(0,13)], 2)# Get ships from the camera her
        self.game = Game(board_size=board_size, ships=self.ships)

    def get_ships(self) -> list[Ship]:
        """
        Converts raw ship data from the camera into Ship objects.
        Each ship is a list of coordinates.
        """
        camera_ships = [[(0,0),(0,1),(0,2)],[(0,11),(0,12),(0,13)]] #self.camera.read_ships() #Read ships from camera here
        ships: list[Ship] = []

        for sections in camera_ships:
            if not sections:
                continue

            # Determine player by position on board. Unsure if we should check x or y here.
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

    def run(self):
        """
        Main game loop.
        """
        while True:
            print(f"Player {self.game.current_player()}'s turn")

            guess = # Read guess from camera here
            # Standin input from the commandline
            try:
                raw_input = input("Enter your guess (x,y): ").strip()
                x_str, y_str = raw_input.split(",")
                guess = (int(x_str), int(y_str))
            except ValueError:
                print("Invalid input format. Please enter coordinates like '3,5'.\n")
                continue
                if not guess:
                    continue

            result = self.game.make_guess(guess)

            print(f"Guess at {guess}: {result.value}")

            if result == GuessReturn.finished_game:
                print(f"Game Over! Player {self.game.current_player()} wins! ")
                break
            print(result)
