#!/usr/bin/env python3
# -*- coding: utf-8 -*-

## @file sensor.py
# @brief Funcionalidades para los sensores de manera genérica. Contiene la clase Sensor, que hereda de Thread, la cual es usada como padre para todos los sensores, estableciendo un esquema multihilo. Se define una función callback para las mediciones de todos los sensores.
# @see config/config.py

import time, _thread

## @class Sensor
# @brief Esta clase hereda de Thread. Es utilizada como padre por todos los sensores. Establece funcionalidades básicas para los sensores, permitiendo la pausa y la reanudación.
class Sensor():
    ## @brief Constructor de la clase
    def __init__(self):
        ## Semáforo para acceder a recursos del hilo desde afuera
        self.runSem     = _thread.allocate_lock()        
        ## Flag para saber si está ejecutandose
        self.running 	= False			                
        ## Flag para saber si se está deteniendo
        self.stopping 	= False			                
    
    ## @brief Establece que el hilo ha comenzado a ejecutarse
    def startSensor(self):
        #Adquiere control del hilo
        self.startCritical()

        #Actualiza estado del sensor
        self.running = True

        #Libera control del hilo
        self.stopCritical()
    
    ## @brief Establece que el hilo se ha detenido
    def endSensor(self):
        #Adquiere control del hilo
        self.startCritical()

        #Actualiza estado del sensor
        self.stopping 	= False
        self.running 	= False

        #Libera control del hilo
        self.stopCritical()
    
    ## @brief Espera a que el hilo reanude su ejecución
    def waitForActivation(self):
        #Espera a que se requiera la ejecución del hilo
        while(not self.isRunning()):
            time.sleep(1)
    
    ## @brief Ordena detener el hilo en el próximo ciclo.
    def stop(self):
        #Adquiere control del hilo
        self.startCritical()

        self.stopping = True

        #Libera control del hilo
        self.stopCritical()
    
    ## @brief Pregunta si el hilo se está deteniendo
    #
    # @params[out] stopping Bandera que indica si el hilo se está deteniendo
    def isStopping(self):
        return self.stopping
    
    ## @brief Pregunta si el hilo está ejecutandose
    #
    # @params[out] running Bandera que indica si el hilo se está ejecutando
    def isRunning(self):
        return self.running

    ## @brief Adquiere control del hilo mediante un semáforo
    def startCritical(self):
        self.runSem.acquire()
    
    ## @brief Libera control del hilo mediante un semáforo
    def stopCritical(self):
        self.runSem.release()
    
    ## @brief Ordena reanudar el hilo en el próximo ciclo.
    def resume(self):
        #Adquiere control del hilo
        self.startCritical()

        self.running = True

        #Libera control del hilo
        self.stopCritical()
    
    def join(self):
        while(self.isRunning()):
            time.sleep(1)

# ## @brief Función callback para los sensores. Genera paquetes de telemetría con las mediciones. Informa si no se ha podido medir alguna variable de algun sensor.
# # @param[in] sensorObj Sensor que llama a la función luego de medir
# # @param[in] **kwargs Colas multiproceso para envíar telemetrias e informar de fallas en la medición.
# # 						kwargs es un diccionario con el siguiente formato: {"queue": q, "stateQueue": rgbqueue}. Donde "queue" es la cola para publicación de telemetrías y 
# # 						"stateQueue" es la cola para la actualización de estado.
# def onRead(sensorObj, **kwargs):
#     if "queue" in kwargs.keys():
#         #Obtiene cola multiproceso
#         q 			= kwargs["queue"]

#         #Obtiene manejador estado dispositivo
#         stateQ	= kwargs["stateQueue"]

#         #Obtiene logger
#         logger      = kwargs["logger"]

#         #Obtiene marca de tiempo en unix y timestamp str
#         #Thingsboard acepta tiempo unix en milisegundos
#         unix 		= np.datetime64(datetime.utcnow(), dtype='datetime64[ms]').astype('float64')/1000 
#         timestamp 	= str(np.datetime64('now')).replace('T', ' ')

#         #Carga configuraciones bateria
#         battery = config.getBattery()

#         #Carga configuraciones del sensor
#         sensor = config.getSensor(sensorObj.name)
#         if not sensor is None:
#             measuring = True
#             for measurement in sensor["measurements"]:
#                 #Obtiene valor de la medición en base a mediana
#                 buff = list(sorted(getattr(sensorObj, measurement["obj_attr_name"])))
#                 if len(buff)>0:                                                                          
#                     #Extrae mediana de las mediciones
#                     value 									= statistics.median(buff)

#                     #Construye paquete completo de telemetria, basandose en plantilla de configuración
#                     telemetry 								= measurement["format"].copy()
#                     tipo = ':'.join(telemetry["tipo"].split(':')[:-1])
#                     telemetry["medicion:%s"%tipo] 			= telemetry["medicion:%s"%tipo]%(value)
#                     telemetry["fecha:%s"%tipo] 				= "%d"%int(unix)

#                     #Construye paquete simple de telemetria
#                     sensorData 									= dict()
#                     sensorData["values"] 						= dict()
#                     sensorData["values"][measurement["name"]] 	= value
#                     sensorData["ts"] 							= unix

#                     #Coloca la medición en formato simple y completo en la cola para poder ser procesada por los publicadores
#                     q.put({"simple": sensorData, "complete": telemetry})

#                     #Verifica estado de las baterias
#                     if sensor["name"] == battery["sensor"] and measurement["name"] == battery["field"]:
#                         if value >= 4.08:
#                             stateQ.put({
#                                 "attribute": "battery-level",
#                                 "state": "full"
#                             })
#                             # device.setBatteryLevel('full')
#                         elif value >= 3.5:
#                             # device.setBatteryLevel('medium')
#                             stateQ.put({
#                                 "attribute": "battery-level",
#                                 "state": "medium"
#                             })
#                         else:
#                             # device.setBatteryLevel('low')
#                             stateQ.put({
#                                 "attribute": "battery-level",
#                                 "state": "low"
#                             })
#                     #Manda mensaje de debugueo
#                     logger.debug("%s | Data obtenida de %s. %s: %s"%(timestamp, sensor["name"], measurement["name"], telemetry["medicion:%s"%tipo]))
#                 else:
#                     #No hay mediciones
#                     measuring = False
#             if not measuring:
#                 #Indica que existe un sensor con al menos una medición que no se está realizando
#                 stateQ.put({
#                                 "attribute": "measuring",
#                                 "state": False
#                             })
#         else:
#             logger.warning("Configuración para sensor %s no encontrada"%(sensorObj.name))
#     else:
#         logger.error("No existe cola en la que publicar mediciones")
