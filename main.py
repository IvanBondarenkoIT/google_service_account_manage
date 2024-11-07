from decouple import config
from google_drive_manager import GoogleDriveManager


# Укажите путь к вашему JSON-файлу с учетными данными
SERVICE_ACCOUNT_FILE = config("SERVICE_ACCOUNT_FILE")
# Учетная запись администратора или пользователя с доступом к файлам
DELEGATED_USER = config("DELEGATED_USER")
# ID главной папки на Google Диске
# для которой будет запущен процесс удаления доступа по ссылке
# ['https://www.googleapis.com/auth/drive']
SCOPES = config("SCOPES")


if __name__ == "__main__":
    gdm = GoogleDriveManager(service_account_file=SERVICE_ACCOUNT_FILE,
                             main_folder_id=SCOPES,
                             delegated_user_email=DELEGATED_USER,
                             )
    gdm.remove_sharing_from_main_folder()
