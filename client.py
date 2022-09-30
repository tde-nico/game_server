import json
import threading
import socket


class Client:
	def __init__(self, server_host, server_port_tcp=1234, server_port_udp=1234, client_port_udp=1235):
		self.identifier = None
		self.server_message = []
		self.room_id = None
		self.client_udp = ('0.0.0.0', client_port_udp)
		self.lock = threading.Lock()
		self.server_listener = SockThread(self.client_udp, self, self.lock)
		self.server_listener.start()
		self.server_udp = (server_host, server_port_udp)
		self.server_tcp = (server_host, server_port_tcp)
		self.register()
	
	def create_room(self, room_name=None):
		message = json.dumps({'action': 'create', 'payload': room_name, 'identifier': self.identifier})
		self.room_id = self.send_to_server(message)

	def join_room(self, room_id):
		self.room_id = room_id
		message = json.dumps({'action': 'join', 'payload': room_id, 'identifier': self.identifier})
		self.room_id = self.send_to_server(message)

	def autojoin(self):
		message = json.dumps({"action": "autojoin", "identifier": self.identifier})
		self.room_id = self.send_to_server(message)

	def leave_room(self):
		message = json.dumps({"action": "leave", "room_id": self.room_id, "identifier": self.identifier})
		self.send_to_server(message)

	def get_rooms(self):
		message = json.dumps({"action": "get_rooms", "identifier": self.identifier})
		message = self.send_to_server(message)
		return message

	def register(self):
		message = json.dumps({"action": "register", "payload": self.client_udp[1]})
		self.identifier = self.send_to_server(message)

	def send_to_server(self, message):	
		self.sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock_tcp.connect(self.server_tcp)
		self.sock_tcp.send(message.encode())
		data = self.sock_tcp.recv(1024)
		self.sock_tcp.close()
		message = self.parse_data(data)
		return message

	def send(self, message):
		message = json.dumps({
			"action": "send",
			"payload": {"message": message},
			"room_id": self.room_id,
			"identifier": self.identifier})
		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		sock.sendto(message.encode(), self.server_udp)

	def sendto(self, recipients, message):
		message = json.dumps({
			"action": "sendto",
			"payload": {
				"recipients": recipients,
				"message": message},
			"room_id": self.room_id,
			"identifier": self.identifier})
		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		sock.sendto(message.encode(), self.server_udp)

	def parse_data(self, data):
		try:
			data = json.loads(data)
			if data['success'] == 'True':
				return data['message']
			else:
				raise Exception(data['message'])
		except ValueError:
			print(data)
	
	def get_messages(self):
		message = self.server_message
		self.server_message = []
		return set(message)

	def stop(self):
		self.server_listener.stop()
		self.server_listener.join()



class SockThread(threading.Thread):
	def __init__(self, addr, client, lock):
		threading.Thread.__init__(self)
		self.client = client
		self.lock = lock
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.sock.bind(addr)
		self.is_running = True
	
	def run(self):
		while self.is_running:
			try:
				data, addr = self.sock.recvfrom(1024)
				self.lock.acquire()
				try:
					self.client.server_message.append(data)
				finally:
					self.lock.release()
			except OSError:
				pass
	
	def stop(self):
		self.is_running = False
		self.sock.close()




if __name__ == '__main__':

	client = Client('127.0.0.1', 1234, 1234, 1235)
	client2 = Client("127.0.0.1", 1234, 1234, 1236)
	client3 = Client("127.0.0.1", 1234, 1234, 1237)
	print("Client 1 : %s" % client.identifier)
	print("Client 2 : %s" % client2.identifier)
	print("Client 3 : %s" % client3.identifier)

	client.create_room("Test room")
	print("Client1 create room  %s" % client.room_id)

	rooms = client.get_rooms()
	selected_room = None
	if rooms is not None and len(rooms) != 0:
		for room in rooms:
			print("Room %s (%d/%d)" % (room["name"], int(room["nb_players"]), int(room["capacity"])))
		selected_room = rooms[0]['id']
		print(selected_room)
	else:
		print("No rooms")


	try:
		client2.join_room(selected_room)
		client3.autojoin()
	except Exception as e:
		print("Error : %s" % str(e))
	print("Client 2 join %s" % client2.room_id)
	print("Client 3 join %s" % client3.room_id)

	client.send({"name": "John", "message": "I'm just John"})
	client2.sendto(client.identifier, {"name": "SUS", "message": "MIMMI"})
	client3.send({"name": "mogus", "message": "hello"})

	for i in range(10):
		#  Send message to room (any serializable data)
		client.send({"name": "A",
					  "message": "AAA"})
		client2.sendto(client.identifier, {"name": "B",
					  "message": "BBB"})
		client3.send({"name": "C",
					  "message": "CCC"})

		# get server data (only client 3)
		message = client.get_messages()
		if len(message) != 0:
			for message in message:
				message = json.loads(message)
				sender, value = message.popitem()
				print(i)
				print("%s say %s" % (value["name"], value["message"]))
	
	print('Leaving...')
	client.leave_room()
	client2.leave_room()
	client3.leave_room()


	client.stop()
	client2.stop()
	client3.stop()

