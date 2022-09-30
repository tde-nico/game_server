import uuid
from player import Player


class Rooms:
	def __init__(self, capacity=2):
		self.rooms = {}
		self.players = {}
		self.room_capacity = capacity

	def register(self, addr, udp_port):
		player = None
		for registered_player in self.players.values():
			if registered_player.addr == addr:
				player = registered_player
				player.udp_addr((addr[0], udp_port))
				break
		if player is None:
			player = Player(addr, udp_port)
			self.players[player.identifier] = player
		return player

	def join(self, player_identifier, room_id=None):
		if player_identifier not in self.players:
			raise ClientNotRegistered()
		player = self.players[player_identifier]

		if room_id is None:
			for room_id in self.rooms.keys():
				if not self.rooms[room_id].is_full():
					self.rooms[room_id].players.append(player)
					return room_id
					break
			room_id = self.create()
			self.join(player_identifier, room_id)
			return room_id
		
		elif room_id in self.rooms:
			if not self.rooms[room_id].is_full():
				self.rooms[room_id].players.append(player)
				return room_id
			else:
				raise RoomFull()
		else:
			raise RoomNotFound()
	
	def leave(self, player_identifier, room_id):
		if player_identifier not in self.players:
			raise ClientNotRegistered()
		player = self.players[player_identifier]
		if room_id in self.rooms:
			self.rooms[room_id].leave(player)
		else:
			raise RoomNotFound()
	
	def create(self, room_name=None):
		identifier = str(uuid.uuid4())
		self.rooms[identifier] = Room(identifier, self.room_capacity, room_name)
		return identifier

	def remove_empty(self):
		for room_id in list(self.rooms.keys()):
			if self.rooms[room_id].is_empty():
				del self.rooms[room_id]

	def send(self, identifier, room_id, message, sock):
		if room_id not in self.rooms:
			raise RoomNotFound()
		room = self.rooms[room_id]
		if not room.is_in_room(identifier):
			raise NotInRoom()
		for player in room.players:
			if player.identifier != identifier:
				player.send_udp(identifier, message)

	def sendto(self, identifier, room_id, recipients, message, sock):
		if room_id not in self.rooms:
			raise RoomNotFound()
		room = self.rooms[room_id]
		if not room.is_in_room(identifier):
			raise NotInRoom()
		if isinstance(recipients, str):
			recipients = [recipients]
		for player in room.players:
			if player.identifier in recipients:
				player.send_udp(identifier, message)



class Room:
	def __init__(self, identifier, capacity, room_name):
		self.capacity = capacity
		self.players = []
		self.identifier = identifier
		if room_name is not None:
			self.name = room_name
		else:
			self.name = self.identifier

	def join(self, player):
		if not self.is_full():
			self.players.append(player)
		else:
			raise RoomFull()

	def leave(self, player):
		if player in self.players:
			self.players.remove(player)
		else:
			raise NotInRoom()

	def is_empty(self):
		if len(self.players) == 0:
			return True
		return False
	
	def is_full(self):
		if len(self.players) >= self.capacity:
			return True
		return False

	def is_in_room(self, player_identifier):
		in_room = False
		for player in self.players:
			if player.identifier == player_identifier:
				in_room = True
				break
		return in_room



class RoomFull(Exception):
	pass

class RoomNotFound(Exception):
	pass

class NotInRoom(Exception):
	pass

class ClientNotRegistered(Exception):
	pass

