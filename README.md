# Immersive battleships
This is the repository for the BSc project Immersive Battleships, created by Nicolaj Auerbach Nielsen, Lasse Nørbjerg, and Rasmus Kjersgaard Bak.\
The project has been made with integration to the air table and requires both the air table and a camera to be connected to the computer for the intended gameplay experience.

## Installing required packages
All the packages required to run the project are listed in `requirements.txt`. To install all of the packages we suggest running:
```
pip install -r requirements.txt
```

## Running the game:
The game can be run via the entrypoint located in main.py with the command:
```
python3 main.py 
```
Before running the game, you need to make sure that the `hardware_variables.py` file has been updated to match your environment. This means changing the following:
- `Port` - This is the port for the arduino of the air table. Help to finding your port can be found [Here](https://www.mathworks.com/help/matlab/supportpkg/find-arduino-port-on-windows-mac-and-linux.html)
- `CameraNum` - This is the camera number of the connected camera you wish to use for the camera integration.
- `TableActive` - This tells the battleship game if the air table is connected. If set to true the battleship game will attempt to create an instance of the Table class and try to send commands to the air table arduino.

When running the game a UI will be shown on the computer, which is in place to help players keep track of guesses and game state.

## Developer mode:
The game has a developer mode which initializes the game without using the camera integration. To run the game in developer mode, you add the `-dev` flag:
```
python3 main.py -dev
```

## Testing:
A small suite of unit tests have been written for the core functionality of the battleship game. These tests are located in the `tests/`directory. These can be run from the root of the project using:
```
python3 -m tests.battleship_tests -b
```
