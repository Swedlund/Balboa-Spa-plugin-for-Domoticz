import sys
import crc8
import logging
import socket

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)


class SpaClient:

	def __init__(self, socket):
		self.s = socket
		self.light = False
		self.current_temp = 0
		self.hour = 12
		self.minute = 0
		self.heating_mode = ""
		self.temp_scale = ""
		self.temp_range = ""
		self.pump1 = ""
		self.pump2 = ""
		self.set_temp = 0
		self.read_all_msg()
		self.priming = False
		self.time_scale = "12 Hr"
		self.heating = False

	s = None

	@staticmethod
	def get_socket(hostname):
		if SpaClient.s is None:
			SpaClient.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			SpaClient.s.connect((hostname, 4257))
			SpaClient.s.setblocking(0)
		return SpaClient.s

	def handle_status_update(self, byte_array):
		self.priming = byte_array[1] & 0x01 == 1
		self.hour = byte_array[3]
		self.minute = byte_array[4]
		flag2 = byte_array[5]
		self.heating_mode = 'Ready' if (flag2 & 0x03 == 0) else 'Rest'
		flag3 = byte_array[9]
		self.temp_scale = 'Farenheit' if (flag3 & 0x01 == 0) else 'Celsius'
		self.time_scale = '12 Hr' if (flag3 & 0x02 == 0) else '24 Hr'
		flag4 = byte_array[10]
		self.heating = 'Off' if (flag4 & 0x30 == 0) else 'On'
		self.temp_range = 'Low' if (flag4 & 0x04 == 0) else 'High'
		pump_status = byte_array[11]
		self.pump1 = ('Off', 'Low', 'High')[pump_status & 0x03]
		self.pump2 = ('Off', 'Low', 'High')[pump_status >> 2 & 0x03]
		self.light = 'On' if (byte_array[14] == 3) else 'Off'
		if byte_array[2] == 255:
			self.current_temp = 0.0 
			self.set_temp = 1.0 * byte_array[20]
		elif self.temp_scale == 'Celsius':
			self.current_temp = byte_array[2] / 2.0
			self.set_temp = byte_array[20] / 2.0
		else:
			self.current_temp = 1.0 * byte_array[2]
			self.set_temp = 1.0 * byte_array[20]

	def get_set_temp(self):
		return self.set_temp

	def get_pump1(self):
		return self.pump1

	def get_pump2(self):
		return self.pump2

	def get_temp_range(self):
		return self.temp_range

	def get_current_time(self):
		return "%d:%02d" % (self.hour, self.minute)

	def get_light(self):
		return self.light

	def get_current_temp(self):
		return self.current_temp

	def string_status(self):
		s = ""
		s = s + "{\n"
		s = s + '"TEMP": "%s",\n"SET_TEMP": "%s",\n"TIME": "%d:%02d",\n' % \
			(format(self.current_temp, '.1f'), format(self.set_temp, '.1f'), self.hour, self.minute)
		s = s + '"PRIMING": "%s",\n"HEATING_MODE": "%s",\n"TEMP_SCALE": "%s",\n"TIME_SCALE": "%s",\n' % \
			(self.priming, self.heating_mode, self.temp_scale, self.time_scale)
		s = s + '"HEATING": "%s",\n"TEMP_RANGE": "%s",\n"PUMP1": "%s",\n"PUMP2": "%s",\n"LIGHTS": "%s"\n' % \
			(self.heating, self.temp_range, self.pump1, self.pump2, self.light)
		s = s + "}\n"
		return s

	def compute_checksum(self, len_bytes, bytes):
		hash = crc8.crc8()
		hash._sum = 0x02
		hash.update(len_bytes)
		hash.update(bytes)
		checksum = hash.digest()[0]
		checksum = checksum ^ 0x02
		return checksum

	def read_msg(self):
		chunks = []
		try:
			len_chunk = self.s.recv(2)
		except:
			return False
		if len_chunk == b'' or len(len_chunk) == 0:
			return False
		length = len_chunk[1]
		try:
			chunk = self.s.recv(length)
		except:
			LOGGER.error("Failed to receive: len_chunk: %s, len: %s",
						 len_chunk, length)
			return False
		chunks.append(len_chunk)
		chunks.append(chunk)

		# Status update prefix
		if chunk[0:3] == b'\xff\xaf\x13':
				# print("Status Update")
				self.handle_status_update(chunk[3:])

		return True

	def read_all_msg(self):
		while (self.read_msg()):
			True

	def send_message(self, type, payload):
		length = 5 + len(payload)
		checksum = self.compute_checksum(bytes([length]), type + payload)
		prefix = b'\x7e'
		message = prefix + bytes([length]) + type + payload + \
			bytes([checksum]) + prefix
		#print(message)
		self.s.send(message)

	def send_config_request(self):
		self.send_message(b'\x0a\xbf\x04', bytes([]))

	def send_toggle_message(self, item):
		# 0x04 - pump 1
		# 0x05 - pump 2
		# 0x06 - pump 3
		# 0x11 - light 1
		# 0x51 - heating mode
		# 0x50 - temperature range

		self.send_message(b'\x0a\xbf\x11', bytes([item]) + b'\x00')

	def set_temperature(self, temp):
		time.sleep(1)                    
		self.read_all_msg() # Read status first to get current temperature unit
		dec = float(temp) * 2.0 if (self.temp_scale == "Celsius") else float(temp)
		self.set_temp = int(dec)
		#print (b'\x0a\xbf\x20', bytes([int(self.set_temp)]))
		self.send_message(b'\x0a\xbf\x20', bytes([int(self.set_temp)]))

	def set_new_time(self, new_hour, new_minute):
		time.sleep(1)                    
		self.new_time = bytes([int(new_hour)]) + bytes([int(new_minute)])
		#print (self.new_time)
		self.send_message(b'\x0a\xbf\x21', (self.new_time))

	def set_pump1(self, value):
		time.sleep(1)                    
		self.read_all_msg() # Read status first to get current pump1 state
		if self.pump1 == value:
			return
		if value == "High" and self.pump1 == "Off":
			self.send_toggle_message(0x04)
			time.sleep(2)
			self.send_toggle_message(0x04)
		elif value == "Off" and self.pump1 == "Low":
			self.send_toggle_message(0x04)
			time.sleep(2)
			self.send_toggle_message(0x04)
		elif value == "Low" and self.pump1 == "High":
			self.send_toggle_message(0x04)
			time.sleep(2)
			self.send_toggle_message(0x04)
		else:
			self.send_toggle_message(0x04)
		self.pump1 = value

	def set_pump2(self, value):
		time.sleep(1)                    
		self.read_all_msg() # Read status first to get current pump2 state
		if self.pump2 == value:
			return
		if value == "High" and self.pump2 == "Off":
			self.send_toggle_message(0x05)
			time.sleep(2)
			self.send_toggle_message(0x05)
		elif value == "Off" and self.pump2 == "Low":
			self.send_toggle_message(0x05)
			time.sleep(2)
			self.send_toggle_message(0x05)
		elif value == "Low" and self.pump2 == "High":
			self.send_toggle_message(0x05)
			time.sleep(2)
			self.send_toggle_message(0x05)
		else:
			self.send_toggle_message(0x05)
		self.pump2 = value
	
import time
try:
	c = SpaClient(SpaClient.get_socket(sys.argv[1]))

	if str(sys.argv[2]) == "status": #status
		time.sleep(1)
		c.read_all_msg()
		print(c.string_status())
	if str(sys.argv[2]) == "lights": #lights toggle
		c.send_toggle_message(0x11) 
	if str(sys.argv[2]) == "pump1": #pump1 off,low,high
		time.sleep(1)
		c.set_pump1(sys.argv[3])
	if str(sys.argv[2]) == "pump2": #pump2 off,low,high
		time.sleep(1)
		c.set_pump2(sys.argv[2])
	if str(sys.argv[2]) == "settemp": #temperature in degrees (C or F)
		c.set_temperature(sys.argv[2])
	if str(sys.argv[2]) == "settime": #hh mm
		new_hour = (sys.argv[3])
		new_minute = (sys.argv[4])
		c.set_new_time(new_hour, new_minute)
	if str(sys.argv[2]) == "heatingmode": #Heat mode toggle for rest or ready
		c.send_toggle_message(0x51)
	if str(sys.argv[2]) == "temprange": #temperature range toggle for high or low
		c.send_toggle_message(0x50)
		time.sleep(1)
		c.read_all_msg()
		print(c.get_temp_range())
except:
	print("Error in spaclient!")