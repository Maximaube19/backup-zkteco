# coding=utf-8

from config import *
from zk import ZK, const
from datetime import datetime
import time
import os
conn = None


# Se crearán objetos de tipo Registro para luego poder ordenarlos por legajo, fecha y hora
class Registro:
        def __init__(self, legajo, fecha):
            self.legajo = legajo # Es el ID de la persona
            self.fecha = fecha


# Diccionario de meses
meses = {1:'enero', 2:'febrero', 3:'marzo', 4:'abril', 5:'mayo', 6:'junio', 7:'julio', 8:'agosto', 
         9:'septiembre', 10:'octubre', 11:'noviembre', 12:'diciembre'}


# Declaro el rango de fechas a filtrar
dia_actual = datetime.today().day
mes_actual = datetime.today().month
anio_actual = anio_siguiente = datetime.today().year
mes_siguiente = mes_actual + 1
if mes_siguiente==13:
    mes_siguiente = 1
    anio_siguiente += 1

date_ini = datetime.strptime('1/{}/{}'.format(mes_actual, anio_actual), '%d/%m/%Y')
date_fin = datetime.strptime('1/{}/{}'.format(mes_siguiente, anio_siguiente), '%d/%m/%Y')



for reloj in RELOJES:

    # Detecto si cambia de mes para hacer el backup del mes anterior completo
    cambiaMes = False

    # Comprueba si existe el directorio con el nombre del edificio, el año y el mes, si no existe lo crea
    if not os.path.exists('{}/{}/{}/{}'.format(RUTA_BACKUP, reloj['EDIFICIO'], anio_actual, meses[mes_actual])):
        os.makedirs('{}/{}/{}/{}'.format(RUTA_BACKUP, reloj['EDIFICIO'], anio_actual, meses[mes_actual]))
        # Si crea una carpeta con el mes quiere decir que está en un mes nuevo
        cambiaMes = True


    # Comprueba si existe el archivo logs.txt, si no existe lo crea con el encabezado 
    if not os.path.exists('{}/{}/logs.txt'.format(RUTA_BACKUP, reloj['EDIFICIO'])):
        log = open('{}/{}/logs.txt'.format(RUTA_BACKUP, reloj['EDIFICIO']),"a")
        log.write('Fecha y Hora\t\tCantidad\tEstado\n---------------------------------------------------------------------------------------------------\n')
        

    # Configuración del archivo txt
    caracteres_legajo = 25
    ruta_archivo = '{}/{}/{}/{}/{}-{}.{}.{}.txt'.format(RUTA_BACKUP, reloj['EDIFICIO'], anio_actual, meses[mes_actual], reloj['EDIFICIO'], dia_actual, meses[mes_actual], anio_actual)
    ruta_log = '{}/{}/logs.txt'.format(RUTA_BACKUP, reloj['EDIFICIO'])


    # create ZK instance
    zk = ZK(reloj['IP_RELOJ'], port=4370, timeout=5, password=0, force_udp=False, ommit_ping=False)


    # Esta función procesa los registros que se envían como primer parámetro, filtrando por las fechas enviadas
    # como segundo y tercer parámetro y genera un archivo txt en la ruta especificada como cuarto parámetro
    def procesarRegistros(asistencias, fecha_inicial, fecha_final, ruta, mensaje_log):
    	registros = []
    	for asistencia in asistencias:
    		if asistencia.timestamp >= fecha_inicial and asistencia.timestamp < fecha_final:
    			registros.append(Registro(int(asistencia.user_id), asistencia.timestamp))

        # Se ordenan los registros por fechas y luego por legajos
    	registros.sort(key=lambda x: x.fecha)
    	registros.sort(key=lambda x: x.legajo)

        # Abre el archivo en modo solo escritura
    	file = open(ruta,"w") 
    	array = ['{:<25}{}'.format('No.','Fecha/Hora\n')] 
        
    	for registro in registros:
    		array.append('{:<25}{}\n'.format(registro.legajo,datetime.strftime(registro.fecha, "%d/%m/%Y %H:%M:%S")))

    	file.writelines(array) 
    	file.close() 

        # Abre el archivo logs para escribir al final
    	log = open(ruta_log,"a") 
    	array_logs = [
    	str(datetime.strftime(datetime.today(), "%d/%m/%Y %H:%M:%S")),
    	'\t'+ str(len(registros)),
    	'\t\t'+mensaje_log,
    	'\n---------------------------------------------------------------------------------------------------\n',
    	]
    	log.writelines(array_logs)
    	log.close()


    # Intenta conectarse con el dispositivo
    try:
        # connect to device
        conn = zk.connect()
        # Deshabilita el dispositivo para asegurarse que no lo utilicen mientras se procesa los datos
        conn.disable_device()


        # Descarga todos los registros
        attendances = conn.get_attendance()

        # Habilita el dispositivo nuevamente
        conn.enable_device()

        # Comprueba si está en un nuevo mes, con lo cual debo hacer el backup de mes anterior completo
        if cambiaMes:
            mes_anterior = mes_actual - 1
            if mes_anterior<1:
                mes_anterior = 12
                anio_anterior = anio_actual - 1
            else:
                anio_anterior = anio_actual
            # Compruebo si existe el directorio del mes anterior, sino lo creo
            if not os.path.exists('{}/{}/{}/{}'.format(RUTA_BACKUP, reloj['EDIFICIO'], anio_anterior, meses[mes_anterior])):
                os.makedirs('{}/{}/{}/{}'.format(RUTA_BACKUP, reloj['EDIFICIO'], anio_anterior, meses[mes_anterior]))
                
            fecha_anterior_ini = datetime.strptime('1/{}/{}'.format(mes_anterior, anio_anterior), '%d/%m/%Y')
            fecha_anterior_fin = datetime.strptime('1/{}/{}'.format(mes_actual, anio_actual), '%d/%m/%Y')
            ruta_nueva = '{}/{}/{}/{}/{}-completo-{}{}.txt'.format(RUTA_BACKUP, reloj['EDIFICIO'], anio_anterior, meses[mes_anterior], reloj['EDIFICIO'], meses[mes_anterior], anio_anterior)
            # Procesa los registros del mes anterior completo
            procesarRegistros(attendances, fecha_anterior_ini, fecha_anterior_fin, ruta_nueva, 'Éxito en backup '+meses[mes_anterior]+' mes completo')

        # Procesa los registros del mes actual
        procesarRegistros(attendances, date_ini, date_fin, ruta_archivo, 'Éxito en backup diario '+meses[mes_actual])
        
        
        print('Archivo '+reloj['EDIFICIO']+' generado con éxito!')

        
    except Exception as e:
        
        ###### En caso de que ocurran errores 


        print ("Process terminate : {}".format(e))

        # Guarda en los logs el fallo en el reloj
        log = open(ruta_log,"a") 
        array_logs = [
            str(datetime.strftime(datetime.today(), "%d/%m/%Y %H:%M:%S")),
            '\t-',
            '\t\tFallo: '+str(e),
            '\n---------------------------------------------------------------------------------------------------\n',
        ]
        log.writelines(array_logs)
        log.close()

        # En ocasiones los dispositivos pueden quedar deshabilitados durante el procesamiento, ya sea 
        # por falta de conexión, algún error, etc. Por lo tanto se debe intentar conectar nuevamente para
        # habilitarlo

        # Espera un minuto e intenta conectarse nuevamente para poder habilitar el dispositivo en caso que se haya trabado
        time.sleep(60)
        try:
            # Intenta conectar y habilitar el dispositivo
            conn = zk.connect()
            conn.enable_device()
            print('Se conectó y habilitó el reloj nuevamente')

            # Guarda en los logs la reconexión exitosa
            log = open(ruta_log,"a") 
            array_logs = [
                str(datetime.strftime(datetime.today(), "%d/%m/%Y %H:%M:%S")),
                '\t-',
                '\t\tÉxito en la reconexión del reloj',
                '\n---------------------------------------------------------------------------------------------------\n',
            ]
            log.writelines(array_logs)
            log.close()

        except Exception as e:
            # En caso de no poder reconectar lanza nuevamente la excepcion
            print ("Process terminate : {}".format(e))

            # Guarda en los logs el fallo al reconectar el reloj
            log = open(ruta_log,"a") 
            array_logs = [
                str(datetime.strftime(datetime.today(), "%d/%m/%Y %H:%M:%S")),
                '\t-',
                '\t\tFallo al reconectar el reloj: '+str(e),
                '\n---------------------------------------------------------------------------------------------------\n',
            ]
            log.writelines(array_logs)
            log.close()

    finally:
    	if conn:
    		conn.disconnect()

