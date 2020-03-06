from config import *
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import os
from datetime import datetime


gauth = GoogleAuth()
# Intenta cargar las credenciales guardadas del cliente
gauth.LoadCredentialsFile("mycreds.txt")
if gauth.credentials is None:
    # Si no encuentra las credenciales, pide autenticarse a Google mediante el navegador
    gauth.LocalWebserverAuth()
elif gauth.access_token_expired:
    # Refresca el token en caso de estar expirado
    gauth.Refresh()
else:
    # Inicializa las credenciales guardadas
    gauth.Authorize()
# Guarda las credenciales actuales en un archivo
gauth.SaveCredentialsFile("mycreds.txt")

drive = GoogleDrive(gauth)

# Este método obtiene el listado de archivos de una carpeta de Google Drive y los guarda en un array
# Devuelve el array
def getDriveListFiles(folder_id):
    drive_files = drive.ListFile({'q': "'"+folder_id+"' in parents and trashed=false"}).GetList()
    filelist=[]
    # Guardo en filelist los nombres de los archivos
    for file in drive_files:
        filelist.append('{}'.format(file['title']))
    return filelist

# Crea una carpeta en Google Drive. Recibe el nombre de la carpeta y el id de la carpeta padre
# Devuelve el id de la carpeta creada
def createDriveFolder(folder_title, parent_id):
    folder_metadata = {'title' : folder_title, 'parents': [{'id': parent_id}], 'mimeType' : 'application/vnd.google-apps.folder'}
    folder = drive.CreateFile(folder_metadata)
    folder.Upload()
    return folder['id']

# Crea una carpeta en la raíz de Google Drive. Recibe el nombre de la carpeta
# Devuelve el id de la carpeta creada
def createDriveFolderInRoot(folder_title):
    folder_metadata = {'title' : folder_title, 'mimeType' : 'application/vnd.google-apps.folder'}
    folder = drive.CreateFile(folder_metadata)
    folder.Upload()
    return folder['id']


# Crea el archivo de Google Drive. Recibe el nombre del archivo, el id de la carpeta padre y la ruta local del archivo
def createDriveFile(file_title, parent_id, path):
    file = drive.CreateFile({
    'title': file_title,
    'parents': [{'id': parent_id}]
    })
    file.SetContentFile(path)
    file.Upload()



# Diccionario de meses
months = {1:'enero', 2:'febrero', 3:'marzo', 4:'abril', 5:'mayo', 6:'junio', 7:'julio', 8:'agosto', 
         9:'septiembre', 10:'octubre', 11:'noviembre', 12:'diciembre'}

current_month = datetime.today().month
current_year = datetime.today().year

# Carpeta de Google Drive que utilizamos como root para los backups de los relojes
folder_root = 'BackupRelojes'
folder_root_id = None

# Nombre de la carpeta correspondiente al año actual
folder_year = str(current_year)
folder_year_id = None

# Nombre de la carpeta correspondiente al mes actual
folder_month = months[current_month]
folder_month_id = None


# Sincroniza cada uno de los relojes según los edificios que tengamos creados en config.py
for reloj in RELOJES:

    # Ejemplo: "C:/ZKTime/backup_relojes/corte/2020/febrero"
    local_path = '{}/{}/{}/{}'.format(RUTA_BACKUP, reloj['EDIFICIO'], folder_year, folder_month)

    '''
        Para poder guardar un archivo en una carpeta específica se debe buscar los ID de cada una de
        las carpetas en los niveles anteriores.
        Por ej: Para guardar en BackupRelojes/año/mes primero se debe buscar la carpeta BackupRelojes
        luego con el ID, dentro de esa buscar la carpeta año, y con ese ID buscar la carpeta mes que se encuentre adentro
    '''

    # Busco la carpeta BackupRelojes en la raíz de Google Drive
    existBackupRelojesFolder = False
    folders = drive.ListFile(
        {'q': "title='" + folder_root + "' and mimeType='application/vnd.google-apps.folder' and trashed=false"}).GetList()
    for folder in folders:
        if folder['title'] == folder_root:
            folder_root_id = folder['id']
            existBackupRelojesFolder = True

    # Si no existe la carpeta BackupRelojes, la crea
    if not existBackupRelojesFolder:
        #Create folder
        folder_root_id = createDriveFolderInRoot(folder_root)





    existYearFolder = False
    # Busca las carpetas de años dentro de BackupRelojes
    folders = drive.ListFile({'q': "'"+folder_root_id+"' in parents and trashed=false"}).GetList()
    for folder in folders:
        if folder['title'] == folder_year:
            folder_year_id = folder['id']
            existYearFolder = True

    # Si no existe la carpeta con el año, la crea
    if not existYearFolder:
        #Create folder
        folder_year_id = createDriveFolder(folder_year, folder_root_id)

        # Crear carpetas de de todos los meses del nuevo año hasta el mes actual.
        # Por ej, si estamos en febrero creará las carpetas de enero y febrero
        for n_month in range(1, current_month+1):
            createDriveFolder(months[n_month], folder_year_id)


        # Entra solo si ya existía la carpeta BackupRelojes en Google Drive. Si no existía
        # quiere decir que es la primera vez que se conecta a Google Drive, por lo que no 
        # debería realizar el backup del mes anterior completo
        if existBackupRelojesFolder:

            # Debo subir el backup completo del ultimo mes del año anterior
            folder_last_year = str(current_year-1)
            folder_last_year_id = None
            folders = drive.ListFile({'q': "'"+folder_root_id+"' in parents and trashed=false"}).GetList()
            for folder in folders:
                if folder['title'] == folder_last_year:
                    folder_last_year_id = folder['id']
            
            folder_last_month = months[12]
            folder_last_month_id = None
            folders = drive.ListFile({'q': "'"+folder_last_year_id+"' in parents and trashed=false"}).GetList()
            for folder in folders:
                if folder['title'] == folder_month:
                    folder_last_month_id = folder['id']

            # Obtengo todos los archivos de la carpeta mes anterior
            drive_filelist = getDriveListFiles(folder_last_month_id)

            # Obtengo todos los archivos locales del mes anterior
            local_path_last_month = '{}/{}/{}/{}'.format(RUTA_BACKUP, reloj['EDIFICIO'], folder_last_year, folder_last_month)
            local_files = os.listdir(local_path_last_month)
            for local in local_files:
                # Recorro los archivos locales y pregunto si no están en Google Drive para subirlos
                if local not in drive_filelist :
                    # Crea el archivo de Drive
                    createDriveFile(local, folder_last_month_id, local_path_last_month+"/"+local)
                    print('Subido en mes anterior '+local)


        


    existMonthFolder = False
    # Busca las carpetas de meses dentro de cada año
    folders = drive.ListFile({'q': "'"+folder_year_id+"' in parents and trashed=false"}).GetList()
    for folder in folders:
        if folder['title'] == folder_month:
            folder_month_id = folder['id']
            existMonthFolder = True

    # Si no existe la carpeta con el mes, la crea
    # Quiere decir que cambia de mes
    if not existMonthFolder:
        #Create folder
        folder_month_id = createDriveFolder(folder_month, folder_year_id)

        # Debo subir el backup completo del mes anterior
        folder_last_month = months[current_month-1]
        folder_last_month_id = None
        folders = drive.ListFile({'q': "'"+folder_year_id+"' in parents and trashed=false"}).GetList()
        for folder in folders:
            if folder['title'] == folder_last_month:
                folder_last_month_id = folder['id']

        # Obtengo todos los archivos de la carpeta mes anterior
        drive_filelist = getDriveListFiles(folder_last_month_id)

        # Obtengo todos los archivos locales del mes anterior
        local_path_last_month = '{}/{}/{}/{}'.format(RUTA_BACKUP, reloj['EDIFICIO'], folder_year, folder_last_month)
        local_files = os.listdir(local_path_last_month)
        for local in local_files:
            # Recorro los archivos locales y pregunto si no están en Google Drive para subirlos
            if local not in drive_filelist :
                # Crea el archivo de Drive
                createDriveFile(local, folder_last_month_id, local_path_last_month+"/"+local)
                print('Subido en mes anterior '+local)


    ### Guarda todos los archivos del año y mes actual ###

    # Obtengo todos los archivos de la carpeta mes
    drive_filelist = getDriveListFiles(folder_month_id)

    # Obtengo todos los archivos locales
    local_files = os.listdir(local_path)
    for local in local_files:
    	# Recorro los archivos locales y pregunto si no están en Google Drive para subirlos
        if local not in drive_filelist :
            # Crea el archivo de Drive
            createDriveFile(local, folder_month_id, local_path+"/"+local)
            print('Subido '+local)


    print('\nGoogle Drive sincronizado con éxito!')