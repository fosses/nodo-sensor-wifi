import ujson, os

def readCfg():
	file_partition = "/fc"
	file_name = "cfg.json"
	try:
		if file_name in os.listdir(file_partition):
			file_name = file_partition + "/" + file_name
		else:
			file_name= "cfge.json"
	except Exception as e:
		print("Nose encontro el archivo de config debido a: %s. se importara el archivo por defecto" %(repr(e)))
		file_name= "cfge.json"
	print("Importando archivo de configuracion %s" %file_name)
	with open(file_name) as json_data_file:
		data = ujson.load(json_data_file)
	return data

def findPublisher(publisher_name):
	for pub in publishers():
		if pub["name"] == publisher_name:
			return pub
	return None

def publishers():
	conf = readCfg()
	return conf["publishers"]

def measurements():
	conf = readCfg()
	return conf["measurements"]

def attributes():
	conf = readCfg()
	return conf["attributes"]
	
def readwificfg(): 
	file_name = "/fc/wifi.json"
	with open(file_name) as json_data_file:
		data = ujson.load(json_data_file)
	return data
def readbuses():
	conf = readCfg()
	return conf["buses"]	