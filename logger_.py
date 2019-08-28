import os, utime, sys, ujson
import lib.sdcard as sdcard
import lib.requests as requests
import _time
from ucollections import deque
class Logger:
	PARTITION 	= '/fc'
	DEBUG_FILE	= 'debug.txt'
	INFO_FILE 	= 'info.txt'
	WARNING_FILE= 'warning.txt'
	ERROR_FILE	= 'error.txt'
	WIFI_FILE	= 'wifi.json'
	
	def __init__(self, spi = None, cs = None, telegramToken = None, chatId = None, name = "unnamed"):
		self.spi			= spi
		self.cs				= cs
		self.telegramToken 	= telegramToken
		self.chatId			= chatId
		self.name			= name
		self.msg_active		= False

		try:
			self.sd				= sdcard.SDCard(spi, cs) # Compatible with PCB 
			self.vfs			= os.VfsFat(self.sd)
			os.mount(self.vfs, Logger.PARTITION)			
			self.initialized	= True
			print("SD inicializada")
			
		except Exception as e:
			print("No se pudo montar micro SD")
			self.vfs			= None
			self.initialized	= False
			sys.print_exception(e)
			print(repr(e))
		try:
			if self.name is "unnamed":
				val_cfg				=self.readCfg("cfg.json")
				self.telegramToken 	= val_cfg["msgconf"]["token"]
				self.chatId			= val_cfg["msgconf"]["chat_id"]
				self.name			= val_cfg["attributes"]["nombre"]
				self.msg_active		= True
				print("Cliente de mensajeria configurado correctamente")
		except Exception as e:
			print("No se pudo configurar el cliente de mensajeria debido a: %s" %repr(e))
	def _log(self, file_path, data_str, put_timestamp = True, prefix = None):
		if self.isInitialized():
			try:
				fn = Logger.PARTITION +"/"+ file_path # 'logdev.txt'
				with open(fn,'a') as f:
					if not prefix is None:
						f.write("%s: "%prefix)
					if put_timestamp:
						f.write(_time.now())
					f.write(data_str) 
					f.write("\r\n")
				utime.sleep(0.2)
			except Exception as e:
				print(repr(e))
	def debug(self, data_str):
		self._log(Logger.DEBUG_FILE, data_str, put_timestamp = True, prefix = "DEBUG")
	def info(self, data_str):
		self._log(Logger.INFO_FILE, data_str, put_timestamp = True, prefix = "INFO")
	def warning(self, data_str):
		self._log(Logger.WARNING_FILE, data_str, put_timestamp = True, prefix = "WARNING")			
	def error(self, data_str):
		self._log(Logger.ERROR_FILE, data_str, put_timestamp = True, prefix = "ERROR")
		if self.msg_active:
			data_str= "%s: %s" %(self.name, data_str)
			headers = {'Content-Type': 'application/json','Accept': 'application/json'}
			data 	= {"chat_id": self.chatId, "text": data_str}
			url 	= 'https://api.telegram.org/bot%s/sendMessage'%(self.telegramToken)
			try:
				r = requests.post(url = url, data = ujson.dumps(data), headers = headers)
				return r.status_code == 200
			except Exception as e:
				print("No se pudo enviar mensaje de reporte de error por mensajeria")
				sys.print_exception(e)
	def data(self, file_name, data):
		self._log(file_name, data, put_timestamp = False)
	def isInitialized(self):
		return self.initialized
	def readLinesCbk(self, file_name, cbk):
		print("Intentando publicar datos pendientes de %s..." %file_name)
		if self.vfs is not None:

			#os.mount(vfs, '/fc')
			if (file_name in os.listdir('/fc')):
				fn = '/fc/' + file_name
				print("Publicando datos de: " + file_name)

				# c.connect()
				with open(fn,'r') as f:
					for line in f:
						print("\nPublica diferido: %s" %line.strip('\r\n'))
						if (not cbk(line[line.index("{"):].strip('\r\n'))):
							return True
						# publisher.publish(line.strip('\r\n'), attr)
				# c.disconnect()
				print("Datos de %s publicados correctamente" %file_name)
				return False
				#os.remove(fn)
			else: 
				print("No existe el archivo %s" %file_name)
			#os.umount('/fc')
			#utime.sleep(0.2)
		else:
			print("No hay SD para leer la database " + file_name)
		return True
		
	def close(self):
		if self.vfs is not None:
			os.umount('/fc')
			print("SD Desmontada")
 
	def readCfg(self, file_name):
		import ujson
		
		if self.isInitialized():
			try:
				with open(Logger.PARTITION + "/" + file_name) as json_data_file:
					data = ujson.load(json_data_file)
				return data
			except Exception as e:
				print(repr(e))
				print("Error importando archivo %s" %file)
				return None
		else:
			print("no iniciado")
			return None
	def removeFile(self, filename):
		os.remove(self.PARTITION + "/" +filename)