import utime
from ntptime import settime

def now():
    fch=utime.localtime()
    return str(fch[0])+"-"+str(fch[1])+"-"+str(fch[2])+" "+str(fch[3])+":"+str(fch[4])+":"+str(fch[5])

def setntp(logger = None):
	tact=utime.time()
#	if (tact < 604169904):
	print("Seteando reloj RTC...")
	# host="ntp.shoa.cl"
	timeout = utime.time() + 5
	test = 0
	while True:
		try:
			if (test == 5 or utime.time() > timeout):
				print("No se pudo configurar el reloj mediante NTP")
				# log(vfs,logdev,"No se pudo configurar el reloj mediante NTP")
				if not logger is None:
					logger.debug("No se pudo configurar el reloj mediante NTP")
				break
			settime()
			test = test + 1

		except Exception as e:
			print(repr(e))
			# log(vfs,logdev,repr(e))
			if not logger is None:
				logger.debug(repr(e))
			print("Error al sincronizar el reloj mediante NTP")
			continue
		else:
			print("Reloj RTC sincronizado")
			break
#	else:
#		print("No es necesario sincronizar el reloj")