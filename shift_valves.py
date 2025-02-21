import serial, time
from cobs import cobs
from bitarray import bitarray
from mappings import normal_board_mapping, flipped_mapping, board19_mapping

class Coord(object):
	"""A simple coordinate object representing x/y coordinates. Supports
	comparison with other Coords, tuples, and lists; hashing; and
	addition with other Coord objects, tuples, lists, and numbers."""
	def __init__(self, x, y):
		self.x = x
		self.y = y

	def __repr__(self):
		return "Coord({}, {})".format(self.x, self.y)


	def __hash__(self):
		return hash((self.x, self.y))


	def __add__(self, other):
		if isinstance(other, Coord):
			return Coord(self.x + other.x, self.y + other.y)
		elif isinstance(other, (tuple, list)):
			return Coord(self.x + other[0], self.y + other[1])
		else:
			return Coord(self.x + other, self.y + other)


	def __radd__(self, other):
		return self + other


	def __eq__(self, other):
		if isinstance(other, (tuple, list)):
			return self.x == other[0] and self.y == other[1]
		return self.x == other.x and self.y == other.y


class Board(object):
	"""Represents a single shift register board with a mapping of
	coordinates to pins. Provide a mapping (see the default_mapping
	variable in the code) and/or an offset that will be added to each
	coordinate in the mapping. The offset can be a number, a tuple/list,
	or a Coord object."""
	def __init__(self, offset=None, mapping=None, bid=None, **kwargs):
		"""Mapping should map 8 coordinates to the pins 0-7 (A-H) on the
		shift register via a dict. E.g.: {(0,0): 0, (0,1): 1, ...}

		The board is laid out as follows when viewed with the barrel
		connector towards the bottom-right.
		Key: C[connector number] - [Shift pin label] ([Shift pin bit])

		C4 - E (4) |---| C8 - A (0)
		C3 - F (5) |   | C7 - B (1)
		C2 - G (6) |   | C6 - C (2)
		C1 - H (7) |---| C5 - D (3)
		"""
		self.bits = bitarray(8)

		self.bid = bid

		default_mapping = normal_board_mapping
		if mapping is None:
			mapping = default_mapping

		self.mapping = {Coord(*k): v for k,v in mapping.items()}

		if offset is not None:
			self.offset_mapping(offset)


	def __repr__(self):
		#r = bstr(self.bits, padding=8, rep0='.')
		r = self.bits.to01().replace('0', '.')
		if self.bid is not None:
			return '{}-{}'.format(self.bid, r)
		return r


	def set(self, coord, value):
		try:
			pin = self.mapping[coord]
		except KeyError:
			return False
		self.bits[pin] = value
		return True

	def clear(self):
		self.bits.setall(0)


	def fill(self):
		self.bits.setall(1)


	def offset_mapping(self, other):
		"""Offset the mapping by a given amount."""
		self.mapping = {(k + other): v for k,v in self.mapping.items()}


class Level(object):
	"""Represents one "level" of the display: a set of daisy-chained
	shift-register boards. Multiple Levels could in theory be used to speed up
	communication, but the Table object doesn't support that yet."""


	def __init__(self, data_pin=11, layout=None):
		"""Set up a Level. Set data_pin to the data line that this level
		is attached to (all shift register boards can share the same
		latch/rck and clock/sck lines.)"""
		#Set up a single level with offsets. The Boards are arranged in
		# the same order as they are connected in.
		self.data_pin = data_pin
		if layout:
			self.layout = layout
		else:
			self.layout = [
					Board((12, 8), bid=0),
					Board((12, 4), bid=1),
					Board((12, 0), bid=2,   mapping=board19_mapping),
					Board((10, 0), bid=3,   mapping=flipped_mapping),
					Board((10, 4), bid=4,   mapping=flipped_mapping),
					Board((10, 8), bid=5,   mapping=flipped_mapping),
					Board((8,  8), bid=6),
					Board((8,  4), bid=7),
					Board((8,  0), bid=8),
					Board((6,  0), bid=9,   mapping=flipped_mapping),
					Board((6,  4), bid=10,  mapping=flipped_mapping),
					Board((6,  8), bid=11,  mapping=flipped_mapping),
					Board((4,  8), bid=12),
					Board((4,  4), bid=13),
					Board((4,  0), bid=14),
					Board((2,  0), bid=15,  mapping=flipped_mapping),
					Board((2,  4), bid=16,  mapping=flipped_mapping),
					Board((2,  8), bid=17,  mapping=flipped_mapping),
					Board((0,  8), bid=18),
					Board((0,  4), bid=19),
					Board((0,  0), bid=20)
			]

		self.coord_to_board = {}
		for board in self.layout:
			for coord in board.mapping:
				self.coord_to_board[coord] = board


	def set(self, coord, value):
		"""Set a single coordinate to a value (1/0 or True/False)."""
		if isinstance(coord[0], (list, tuple)):
			for c in coord:
				self.set(c, value)
		else:
			self.coord_to_board[coord].set(coord, value)


	def fill(self):
		for board in self.layout:
			board.fill()


	def clear(self):
		"""Clear all boards to 0"""
		for board in self.layout:
			board.clear()


	def repr_shift_string(self):
		return ' '.join(map(repr, self.layout))


	def get_shift_string(self):
		"""Return a binary string that represents the entire Level that
		can be shifted into the first board."""
		return b''.join([board.bits.tobytes() for board in reversed(self.layout)])


	def shift_str(self):
		"""Return the string to shift out this level on its data pin."""
		return cobs.encode(
			bytes([self.data_pin]) + self.get_shift_string()) + b'\x00'


	def set_and_shift(self, coord, value):
		"""Set a single coordinate to a value and return the shift string."""
		self.set(coord, value)
		return self.shift_str()


class Table:
	def __init__(self, serial_port, baudrate=115200, data_pin=11, layout=None):
		self.serial = serial.Serial(serial_port, baudrate=baudrate)
		self.level = Level(data_pin=data_pin, layout=layout)
		self.serial.write(cobs.encode(bytes([11]) + b'\x00') + b'\x00')


	def set(self, coord, value):
		self.serial.write(self.level.set_and_shift(coord, value))


	def fill(self):
		"""Open all valves."""
		self.level.fill()
		self.serial.write(self.level.shift_str())


	def clear(self):
		"""Close all valves."""
		self.level.clear()
		self.serial.write(self.level.shift_str())


	def send(self):
		self.serial.write(self.level.shift_str())


	def cycle_board(self, board, delay=1):
		"""Toggle on/off all valves in a board."""
		while True:
			print(f'Clear board {board}')
			self.level.layout[board].clear()
			self.send()
			time.sleep(delay)

			print(f'Fill board {board}')
			self.level.layout[board].fill()
			self.send()
			time.sleep(delay)


if __name__ == '__main__':
	import sys
	"""Demonstrate communicating with an attached Arduino for shifting
	one level at a time."""

	if not sys.argv[1:]:
		print(f'Usage: {sys.argv[0]} serial_port', file=sys.stderr)
		sys.exit(0)

	l0 = Level(11, layout=[Board((0,0))])
	ser = serial.Serial(sys.argv[1], baudrate=115200)

	ser.write(cobs.encode(bytes([11]) + b'\x00') + b'\x00')

	val = True
	while True:
		for y in range(0,4):
			for x in range(0,2):
				print(f'({x}, {y} -> {val})')
				input()  #wait for the Enter key
				l0.set((x,y), val)
				ser.write(l0.shift_str())
		val = not val
