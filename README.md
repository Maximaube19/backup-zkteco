# Backup Relojes ZKTeco

El programa realiza una copia diaria de los registros del reloj ZKTeco filtrados por mes y año y ordenados por ID y fecha.
Además genera un archivo de logs registrando cada evento.
También sincroniza los archivos generados localmente con Google Drive.


## Información del Proyecto

Utiliza las librerías:
* pyzk v0.9 para conexión a relojes biométricos ZKTeco: https://github.com/fananimi/pyzk
* PyDrive v1.3.1 para sincronización con Google Drive: https://github.com/gsuitedevs/PyDrive


### Requisitos

Instalar python 2.7 o superior 

Instalar Virtualenv o Virtualenvwrapper, crear un entorno virtual llamado zk y activarlo

```
$ mkvirtualenv zk
$ C:\Users\ruta_de_los_entornos_virtuales\zk\Scripts\activate
```

Instalar los requerimientos

```
$ cd <ruta_del_directorio>\ZKTeco
$ pip install -r requirements.txt
```

Editar el archivo **config.py**, añadir los relojes (nombre del edificio y la IP del reloj) y establecer la ruta donde se encuentra el directorio "backup_relojes".


## Descripción detallada

La estructura de directorios es la siguiente:

```
<ruta_del_directorio>
		|- ZKTeco
			|
			|- backup_relojes
			|
			|- files_backup
				|
				|- backup.py
				|- sinc_zk.py
				|- (otros archivos)
				|- backup_zk.bat
				|- ejecuta_bat_zk.VBScript
```

El archivo "config.py" contiene configuraciones básicas sobre ruta de archivos, relojes, etc.

El archivo "backup.py" contiene los procedimientos para conectarse al reloj, procesar la información y generar las copias diarias de los registros.

El archivo "sinc_zk.py" contiene los procedimientos para sincronizar los archivos locales con Google Drive en la cuenta con la que se inicia sesión.



### Backup diario de relojes ZKTeco

Dentro del directorio backup_relojes se creará una carpeta por cada "EDIFICIO" que sea asignado, dentro de este se crearán directorios con el año y el mes. Dentro del directorio del mes se creará automaticamente un archivo con los registros del reloj de cada día y se registrarán los eventos en el archivo logs.
Al cambiar a un nuevo mes, además de generar el archivo del día actual del nuevo mes, se creará un archivo con el backup completo del mes anterior.

Ejemplo de la estructura de directorios resultante:

```
<ruta_del_directorio>
		|- ZKTeco
			|
			|- backup_relojes
			|		|- edificio_principal
			|			|- 2020
			|			|	|- enero
			|			|	|	|- (todos los archivos de enero)
			|			|	|- febrero
			|			|		|- edificio_principal-1.febrero.2020
			|			|		|- (todos los archivos del mes)
			|			|		|- edificio_principal-28.febrero.2020
			|			|		|- edificio_principal-completo-febrero.2020
			|			|	|- marzo
			|			|		|- edificio_principal-1.marzo.2020
			|			|- logs.txt
			|			
			|
			|- files_backup
				|
				|- backup.py
				|- sinc_zk.py
				|- (otros archivos)
				|- backup_zk.bat
				|- ejecuta_bat_zk.VBScript
```

Para que se ejecute diariamente y automáticamente se recomienda crear un script que ejecute los archivos backup.py y sinc_kz.py. Luego programar una tarea en el sistema operativo para que se ejecute diariamente. 
A modo de ejemplo les dejo archivos para Windows backup_zk.bat y sincronizar_drive.bat, los cuales ejecutarán los archivos de Python.


### Sincronizar con Google Drive

* **Autenticación**
Drive API requiere OAuth2.0 para la autenticación.

Siga estos pasos:
1. Vaya a la [consola de API](https://console.developers.google.com/iam-admin/projects) y cree su propio proyecto.
2. Busque 'API de Google Drive', seleccione la entrada y haga clic en 'Habilitar'.
3. Seleccione 'Credenciales' en el menú de la izquierda, haga clic en 'Crear credenciales', seleccione 'ID de cliente OAuth'.
4. Ahora, debe configurar el nombre del producto y la pantalla de consentimiento -> haga clic en 'Configurar pantalla de consentimiento' y siga las instrucciones. Una vez terminado:
	a. Seleccione 'Tipo de aplicación' para ser aplicación web .
	b. Ingrese un nombre apropiado.
	c. Haz clic en "Crear".
5. Haga clic en 'Descargar JSON' en el lado derecho de ID de cliente para descargar **client_secret_ID_muy_larga.json .**

El archivo descargado tiene toda la información de autenticación de su aplicación. **Cambie el nombre del archivo a "client_secrets.json" y colóquelo en su directorio de trabajo.**


* **Funcionamiento**

En el archivo **sinc_zk.py** verá el siguiente código:

```
gauth = GoogleAuth()
gauth.LoadCredentialsFile("mycreds.txt")
if gauth.credentials is None:
    gauth.LocalWebserverAuth()
elif gauth.access_token_expired:
    gauth.Refresh()
else:
    gauth.Authorize()
gauth.SaveCredentialsFile("mycreds.txt")
```

Intenta cargar las credenciales del cliente guardadas localmente en "mycreds.txt". Si el archivo no existe (ocurrirá la primera vez) abrirá el navegador y pedirá autenticación con la cuenta de Google correspondiente, luego se guadarán las credenciales localmente para no volver a pedir autenticación con el navegador.



El programa crea en Google Drive un directorio llamado "BackupRelojes", y tendrá adentro la siguiente estructura:

```
BackupRelojes
	|- 2020
		|- Enero
		|- Febrero
		|- Marzo
```

Accede al año y mes actual, obtiene el listado de archivos y los compara con los archivos locales. Si encuentra alguno que no esté sincronizado, lo sube.

En caso de cambiar a un nuevo mes, luego de crear el directorio del nuevo mes y subir sus archivos, revisa el mes anterior para corroborar si hubo archivos que faltaron de subir.


Espero que les sirva 🤓