# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)
import gc, webrepl, esp, time
from logger_ import Logger
from machine import SPI, Pin, unique_id

esp.osdebug(None)
gc.collect()

spi 	= SPI(sck = Pin(14), mosi = Pin(13), miso = Pin(15))
cs 		= Pin(5, Pin.OUT)
time.sleep(0.2)
cfg = Logger(spi = spi, cs = cs)
time.sleep(0.2)
wficfg=cfg.readCfg('wifi.json')

def get_id():
	x = [hex(int(c)).replace("0x","") for c in unique_id()]
	for i in range(len(x)):                                                                                                                           
		if len(x[i]) == 1:
			x[i] = "0"+x[i]
	return ''.join(x)
  
def do_connect():
	import network
	wlan = network.WLAN(network.STA_IF) # create station interface
	wlan.active(True)	   # activate the interface
	wlan.config(dhcp_hostname="ESP32_NODO_" + get_id())
	if not wlan.isconnected():	  # check if the station is connected to an AP
		wlan.connect(wficfg["ssid"], wficfg["pssw"]) # connect to the AP (Router)
#		wlan.connect("WSLAB", "wslabufro") # connect to the AP (Router)
		#wlan.connect("BlackBOX", "familia@323435")
		#wlan.connect("HUAWEI", "manzanas")
		for _ in range(12):
			if wlan.isconnected():	  # check if the station is connected to an AP
				print('network config:', wlan.ifconfig())
				webrepl.start()
				import uftpd
				break
			print('.', end='')
			time.sleep(1)
		else:
			print("Connect attempt timed out\n")
			return
	print('\nnetwork config:', wlan.ifconfig())
	


do_connect()
cfg.close()
spi.deinit()
# print('Booted!')

