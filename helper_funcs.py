import math

def eucl_dist(p1: tuple[int, int], p2: tuple[int, int]):
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

def split_coords(board_x_len: int, points: list[tuple[int, int]]):
    """"x_coord is usually something like self.board_size[0]"""
    left_half = [point for point in points if point[0] < board_x_len // 2]
    right_half = [point for point in points if point[0] >= board_x_len // 2]
    if len(left_half) != len(right_half):
        raise ValueError("More ship sections on one side")
    return ((left_half, 1), (right_half, 2))
