from machine import UART,I2C ,Pin, deepsleep, wake_reason, SPI, WDT, freq
#import ssd1306
from publisher_ import Publisher
#from pms7003 import PMS7003
from esp32 import raw_temperature
#from am2315 import *
from logger_ import Logger
import utime, ujson, os, sys, config, _time, sensorpool

versionsw 	= "2.1.0"
tairf 		= 12
tstamp 		= 946684800
logdat 		= 'logdata.txt'
amok 		= 0
hmok 		= 0
pmok 		= 0

if __name__ == '__main__':
	freq(80000000)
	print("iniciando...")
	print(wake_reason())
	wdt = WDT(timeout=130000)
	# Inicializa habilitación de los sensores de material particulado.
	hpma_pin 	= Pin(16, Pin.OUT) #Se?al de activaci?n de transistor
	pms_pin 	= Pin(4, Pin.OUT) #Se?al de activaci?n de transistor
#	hpma_pin.value(0)
#	pms_pin.value(0)

	# Configura buses de comunicación.
	uart 	= UART(2, baudrate=115200, rx=32, tx=17, timeout=1000)
	i2c 	= I2C(sda = Pin(21, Pin.PULL_UP), scl = Pin(22,Pin.PULL_UP), freq = 20000)
	spi 	= SPI(sck = Pin(14), mosi = Pin(13), miso = Pin(15))
	cs 		= Pin(5, Pin.OUT)

	#Prueba pantalla oled
	#oled = ssd1306.SSD1306_I2C(128, 64, i2c, 0x3c)
	#oled.fill(0)
	#oled.text("Hello World asdfadsf asd", 0, 0)
	#oled.show()

	# Inicia logger. Interfaz para SD.
	logger = Logger(spi = spi, cs = cs)

	# Sincroniza NTP
	_time.setntp(logger = logger)

	# Inicia sensores
	sensors = sensorpool.startSensors(uart = uart, i2c = i2c, spi = spi, logger = logger, hpma_pin=hpma_pin, pms_pin=pms_pin)

	while True:
		#Marca de tiempo inicio ina219
		# st = utime.ticks_ms()

		#Datasheet says to wait for at least 30 seconds...
		print('Flujo de aire forzado por %d segundos...' %tairf)
		utime.sleep(tairf)
		#Returns NOK if no measurement found in reasonable time
		print('Realizando medicion...')
		
		# Inicializa buffers para mediciones
		HPM2_5,HPM10, PPM2_5, PPM10, tem, hr, SPM2_5, SPM10 =([0.0]*5,[0.0]*5,[0.0]*5,[0.0]*5,[0.0]*5,[0.0]*5,[0.0]*5,[0.0]*5)

		# Lectura de los sensores. 5 mediciones
		for i in range(5):
			try:
	#		# Lee HPMA115S0
				if "hpma115s0" in sensors: 
					sensors["hpma115s0"].readParticleMeasurement()
					HPM2_5[i]	= sensors["hpma115s0"]._pm2_5
					HPM10[i]	= sensors["hpma115s0"]._pm10
			except Exception as e:
				sys.print_exception(e)	
				print(repr(e))
				logger.debug("Error en lectura de sensor honeywell")
				logger.debug(sys.print_exception(e))
			try:
				if "pms7003" in sensors:
	#						# Lee PMS7003
					pms_data 	= sensors["pms7003"].read()
					PPM2_5[i]	= min(max(pms_data['PM2_5'], 0), 1000)
					PPM10[i]	= min(max(pms_data['PM10_0'], 0), 1000)
			except Exception as e:
				sys.print_exception(e)	
				print(repr(e))
				logger.debug("Error en lectura de sensor plantower")
				logger.debug(sys.print_exception(e))
			try:
				# Lee AM2315
				if "am2315" in sensors:
					sensors["am2315"].measure()
					tem[i]		= sensors["am2315"].temperature()
					hr[i]		= sensors["am2315"].humidity()
			except Exception as e:
				sys.print_exception(e)	
				print(repr(e))
				logger.debug("Error en lectura de sensor AM2315")
				logger.debug(sys.print_exception(e))
			try:
				if "am2302" in sensors:
					sensors["am2302"].measure()
					tem[i]		= sensors["am2302"].temperature()
					hr[i]		= sensors["am2302"].humidity()
			except Exception as e:
				sys.print_exception(e)	
				print(repr(e))
				logger.debug("Error en lectura de sensor AM2302")
				logger.debug(sys.print_exception(e))
			try:
				if "sps30" in sensors:
					sensors["sps30"].measure()
					SPM2_5[i]		= sensors["sps30"]._pm2p5
					SPM10[i]		= sensors["sps30"]._pm10
			except Exception as e:
				sys.print_exception(e)	
				print(repr(e))
				logger.debug("Error en lectura de sensor SPS30")
				logger.debug(sys.print_exception(e))

		
		# Apaga sensores de material particulado
		hpma_pin.value(0)
		pms_pin.value(0)

		#Crea publicadores
		publishers = []
		for pub in config.publishers():
			publishers.append(
				Publisher(host = pub["host"], token = pub["token"], port = pub["port"], format_ = pub["format"], logger = logger, wdt=wdt)
			)
		
		## **************** PREPARACIÓN DE PAQUETES DE TELEMETRÍA **************** 
		tstp	= (utime.time()+tstamp)*1000
		fecha	= _time.now()
		HPM2_5	= list(sorted(HPM2_5))
		HPM10	= list(sorted(HPM10))
		PPM10	= list(sorted(PPM10))
		PPM2_5	= list(sorted(PPM2_5))
		tem		= list(sorted(tem))
		hr		= list(sorted(hr))
		SPM2_5	= list(sorted(SPM2_5))
		SPM10	= list(sorted(SPM10))
		
		
		print("PM2.5: %.2f %.2f %.2f ug/m3 [H-P-S]" % (HPM2_5[2], PPM2_5[2], SPM2_5[2]))
		print("PM10:  %.2f %.2f %.2f ug/m3 [H-P-S]" % (HPM10[2], PPM10[2], SPM10[2]))
		print("Temperatura: %.2f ?C" % (tem[2]))
		print("Humedad Rel: %.2f %%" %(hr[2]))
		
		# Finaliza ina219
		sensors["ina219"].stop()
		sensors["ina219"].join()
		
		simple_tel = {}
		simple_tel["tiempo"]	= fecha
		simple_tel["tesp"]		= (raw_temperature()-32)*0.5555556
		simple_tel["hmok"]		= int("hpma115s0" in sensors)
		simple_tel["pmok"]		= int("pms7003" in sensors)
		simple_tel["amok"]		= int("am2315" in sensors or "am2302" in sensors)
		simple_tel["spok"]		= int("sps30" in sensors)

		complete_tel 	= config.measurements()
		attr 			= config.attributes()
		attr["version"] = versionsw
		complete_tel["hm10"]["medicion:contaminante:mp10"]			= HPM10[2]
		complete_tel["hm10"]["fecha:contaminante:mp10"]				= tstp
		complete_tel["hm2_5"]["medicion:contaminante:mp2_5"]		= HPM2_5[2]
		complete_tel["hm2_5"]["fecha:contaminante:mp2_5"]			= tstp
		complete_tel["pm10"]["medicion:contaminante:mp10"]			= PPM10[2]
		complete_tel["pm10"]["fecha:contaminante:mp10"]				= tstp
		complete_tel["pm2_5"]["medicion:contaminante:mp2_5"]		= PPM2_5[2]
		complete_tel["pm2_5"]["fecha:contaminante:mp2_5"]			= tstp
		complete_tel["temp"]["medicion:meteorologia:temperatura"]	= tem[2]
		complete_tel["temp"]["fecha:meteorologia:temperatura"]		= tstp
#		complete_tel["temp"]["tipo"]								= "meteorologia:temperatura:\xbaC"
		complete_tel["hur"]["medicion:meteorologia:humedad"]		= hr[2]
		complete_tel["hur"]["fecha:meteorologia:humedad"]			= tstp
		complete_tel["tesp"]["medicion:otro:temperatura"]			= (raw_temperature()-32)*0.5555556
#		complete_tel["tesp"]["tipo"]								= "meteorologia:temperatura:\xbaC"
		complete_tel["tesp"]["fecha:otro:temperatura"]				= tstp
		complete_tel["sm10"]["medicion:contaminante:mp10"]			= SPM10[2]
		complete_tel["sm10"]["fecha:contaminante:mp10"]				= tstp
		complete_tel["sm2_5"]["medicion:contaminante:mp2_5"]		= SPM2_5[2]
		complete_tel["sm2_5"]["fecha:contaminante:mp2_5"]			= tstp
			
		atrpub=ujson.dumps(attr)
		
		# Vuelve a intentar insertar las telemetrias pendientes desde la bd
		for pub in publishers:
			pub.dbPublish(atrpub)
	
		pub_tel = {}
		pub_tel["tesp"]=complete_tel["tesp"]
		if "hpma115s0" in sensors: 	
			pub_tel["hm2_5"]=complete_tel["hm2_5"]
			pub_tel["hm10"]=complete_tel["hm10"]
			simple_tel["HPM2.5"] 	= HPM2_5[2]
			simple_tel["HPM10"] 	= HPM10[2]
		if "pms7003" in sensors:
			pub_tel["pm2_5"]=complete_tel["pm2_5"]
			pub_tel["pm10"]=complete_tel["pm10"]
			simple_tel["PPM2.5"] 	= PPM2_5[2]
			simple_tel["PPM10"] 	= PPM10[2]			
		if "am2315" in sensors or "am2302" in sensors:
			pub_tel["temp"]=complete_tel["temp"]
			pub_tel["hur"]=complete_tel["hur"]	
			simple_tel["Temp"] 	= tem[2]
			simple_tel["HR"] 		= hr[2]			
		if "sps30" in sensors:
			pub_tel["sm2_5"]=complete_tel["sm2_5"]
			pub_tel["sm10"]=complete_tel["sm10"]
			simple_tel["SPM2_5"]	= SPM2_5[2]
			simple_tel["SPM10"]	= SPM10[2]
		if "ina219" in sensors and sensors["ina219"].voltage is not None:
			simple_tel["voltage"] 	= sensors["ina219"].voltage
			simple_tel["current"] 	= sensors["ina219"].current
			simple_tel["power"] 	= sensors["ina219"].power
			complete_tel["voltage"]["medicion:otro:voltaje"]		= sensors["ina219"].voltage
			complete_tel["voltage"]["fecha:otro:voltaje"]			= tstp
			complete_tel["current"]["medicion:otro:corriente"]		= sensors["ina219"].current
			complete_tel["current"]["fecha:otro:corriente"]			= tstp
			complete_tel["power"]["medicion:otro:potencia"]			= sensors["ina219"].power
			complete_tel["power"]["fecha:otro:potencia"]			= tstp
			pub_tel["voltage"]=complete_tel["voltage"]
			pub_tel["current"]=complete_tel["current"]	
			pub_tel["power"]=complete_tel["power"]	
		
		simple_tel = {
			"ts": tstp,
			"values": simple_tel
		}

		## **************** PUBLICACIÓN DE TELEMETRIAS **************** 

		for pub in publishers:
			try:
				if pub.format == "simple":
					print("\nPublica simple: %s"%ujson.dumps(simple_tel))
					pub.publish(ujson.dumps(simple_tel), atrpub)
				elif pub.format == "complete":
					for meas in pub_tel:
						print("\nPublica completo: %s"%ujson.dumps(pub_tel[meas]))
						pub.publish(ujson.dumps(pub_tel[meas]), atrpub)
				
			except Exception as e:
				sys.print_exception(e)	
				print(repr(e))
				logger.debug("Error en la publicación")
				logger.debug(sys.print_exception(e))
		logger.data(logdat, ujson.dumps(simple_tel))
		logger.close()
		print('Sensor y ESP32 en modo sleep')
#		break
		twking=utime.ticks_ms()
		deepsleep(600000-twking)#10 minutos
	#	deepsleep(20000) #20 segundos
