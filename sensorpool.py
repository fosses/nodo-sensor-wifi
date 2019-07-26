import utime,dht, sys
from machine import Pin
import hpma2, sps30
from am2315 import *
from pms7003 import PMS7003
from ina219_ import INA219_
import _thread

def startSensors(uart = None, i2c = None, spi = None, logger = None, hpma_pin=None, pms_pin=None, **kwargs):

	sensors = dict()

#	hpma_pin 	= Pin(16, Pin.OUT) #Se?al de activaci?n de transistor
	# pms_pin 	= Pin(12, Pin.OUT) #Se?al de activaci?n de transistor

	# Inicia sensor PMS7003
#	try:
#		pms = PMS7003()
#		if(pms.init()):
			# pmok=1
#			sensors["pms7003"] = pms
#	except Exception as e:
#		print(repr(e))

	if not uart is None:
		try:
			print("Inicializando SPS30...")
			hpma_pin.value(1)
			utime.sleep(0.3)
			sps=sps30.SPS30(uart)
			utime.sleep(0.2)
			sps.start()
			utime.sleep(2)
			if(sps.measure()):
				print("SPS30 inicializado")
				sensors["sps30"] = sps
		except Exception as e:
			sys.print_exception(e)	
			print("No se pudo iniciar SPS30")
			hpma_pin.value(0)
			print(repr(e))
			utime.sleep(0.2)

	if not "sps30" in sensors:
		# Inicia HPMA115S0
		tmout = utime.time() + 15   # 15 segundos
		test = 0
		hmok = 0
		while True:
			hpma_pin.value(1)
			try:
				hpma = hpma2.HPMA115S0(uart)
				hpma.init()
				hpma.startParticleMeasurement()
				if (hpma.readParticleMeasurement()):
					# hmok = 1
					print("Honeywell inicializado")
					sensors["hpma115s0"] = hpma
					break
			except Exception as e:
				print(repr(e))
			if (test == 5 or utime.time() > tmout):
				print("No se pudo iniciar Honeywell")
				hpma_pin.value(0)
				utime.sleep(0.5)
				break
			test = test + 1
	if not i2c is None:
		# Inicia sensor AM2315
		tmout = utime.time() + 5   # 5 segundos
		test = 0
		while True:
			try:
				am2315 = AM2315( i2c = i2c )
				print("Iniciando sensor AM2315...")
				if(am2315.measure()):
					print("AM2315 inicializado")
					sensors["am2315"] = am2315	
					break
			except Exception as e:
				sys.print_exception(e)	
				print("No se pudo iniciar AM2315")
				print(repr(e))
				
			if (test == 5 or utime.time() > tmout):
				print("No se pudo iniciar AM2315")
				break
			test = test + 1
		
		try:
			# Inicia sensor INA219
			#Crea hilo para lectura del sensor am2315
			ina219 = INA219_(buffLen = 3, period = 5, sem = None, on_read = None, **kwargs)
			#Comienza lectura del sensor
			_thread.start_new_thread(ina219.run, ())
			sensors["ina219"] = ina219
		except Exception as e:
			sys.print_exception(e)	
			print("No se pudo iniciar INA219")
			print(repr(e))

	if not spi is None:
		pass

	if not "pms7003" in sensors:
		print("iniciando AM2302")
		tmout = utime.time() + 5   # 5 segundos
		test = 0
		while True:
			try:
#			am2302_pin	= Pin(4, Pin.OUT) #Senal de activaci?n de transistor
				pms_pin.value(1)
				utime.sleep(0.1)
				am2302 = dht.DHT22(Pin(2))
				am2302.measure()
				sensors["am2302"] = am2302
#			print(sensors["am2302"].humidity())
#			print(sensors["am2302"].temperature())
				print("Sensor AM2302 inicializado")
				break
			except Exception as e:
				sys.print_exception(e)	
				print(repr(e))
			if (test == 5 or utime.time() > tmout):
				print("No se pudo iniciar AM2302")
				pms_pin.value(0)
#				utime.sleep(0.5)
				break
			test = test + 1
#			pms_pin.value(0)
			utime.sleep(0.5)
	
	return sensors