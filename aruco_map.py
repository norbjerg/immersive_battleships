PLAYER1_GUESS_CONFIRM = 100
PLAYER2_GUESS_CONFIRM = 101

# Note that these are the arucos, that player x will be able to guess on
# Note that when the player is sitting opposite, it will flip the y values, so 13 in airtable system
# will be 0 for the player
PLAYER1_VERTICAL_Y_COORD_TO_ARUCO_ID = {
    10: 13,
    11: 12,
    12: 11,
    13: 10,
    14: 9,
    15: 8,
    16: 7,
}
PLAYER1_HORIZONTAL_X_COORD_TO_ARUCO_ID = {
    17: 0,
    18: 1,
    19: 2,
    20: 3,
    21: 4,
    22: 5,
    23: 6,
    24: 7,
    25: 8,
    26: 9,
    27: 10,
    28: 11,
}

PLAYER2_VERTICAL_Y_COORD_TO_ARUCO_ID = {
    30: 0,
    31: 1,
    32: 2,
    33: 3,
    34: 4,
    35: 5,
    36: 6,
}
PLAYER2_HORIZONTAL_X_COORD_TO_ARUCO_ID = {
    37: 11,
    38: 10,
    39: 9,
    40: 8,
    41: 7,
    42: 6,
    43: 5,
    44: 4,
    45: 3,
    46: 2,
    47: 1,
    48: 0,
}
