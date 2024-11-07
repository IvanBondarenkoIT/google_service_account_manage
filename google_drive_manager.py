from google.oauth2 import service_account
from googleapiclient.discovery import build, Resource
from google.auth.credentials import Credentials


class GoogleDriveManager:
    def __init__(self, service_account_file: str, main_folder_id: str, delegated_user_email: str) -> None:
        """
        Класс для управления доступом к папкам Google Диска с использованием Service Account.
        Позволяет удалять доступ по ссылке для главной папки и всех вложенных папок.

        Аргументы:
            service_account_file (str): Путь к JSON-файлу с учетными данными Service Account.
            main_folder_id (str): ID главной папки на Google Диске, для которой будет запущен процесс удаления доступа по ссылке.
            delegated_user_email (str): Email пользователя для имперсонации.
                                         Service Account будет действовать от имени этого пользователя.

        """
        self.service_account_file = service_account_file
        self.main_folder_id = main_folder_id
        self.delegated_user_email = delegated_user_email
        self.credentials: Credentials = self._authenticate()
        self.drive_service: Resource = build('drive', 'v3', credentials=self.credentials)
        print("Аутентификация успешно выполнена и сервис подключен.")

    def _authenticate(self) -> Credentials:
        """
        Выполняет аутентификацию с использованием Service Account и делегирования прав.

        Возвращает:
            Credentials: Учётные данные с поддержкой имперсонации для доступа к Google Диску.
        """
        print("Аутентификация с использованием Service Account...")
        scopes = ['https://www.googleapis.com/auth/drive']
        credentials = service_account.Credentials.from_service_account_file(
            self.service_account_file, scopes=scopes
        )
        # Настройка имперсонации пользователя
        print(f"Настроена имперсонация для пользователя: {self.delegated_user_email}")
        return credentials.with_subject(self.delegated_user_email)

    def remove_link_sharing(self, folder_id: str) -> None:
        """
        Удаляет доступ по ссылке для указанной папки на Google Диске.

        Аргументы:
            folder_id (str): ID папки на Google Диске, для которой нужно убрать доступ по ссылке.
        """
        print(f"Проверка разрешений для папки ID: {folder_id}...")
        permissions = self.drive_service.permissions().list(fileId=folder_id, fields="permissions(id, type, role)").execute()
        for permission in permissions.get('permissions', []):
            if permission['type'] == 'anyone':
                self.drive_service.permissions().delete(fileId=folder_id, permissionId=permission['id']).execute()
                print(f"Удален доступ по ссылке для папки ID: {folder_id}")

    def traverse_and_remove_sharing(self, parent_folder_id: str = None) -> None:
        """
        Рекурсивно обходит вложенные папки и удаляет доступ по ссылке.

        Аргументы:
            parent_folder_id (str, optional): ID родительской папки. Если None, используется main_folder_id.
        """
        if parent_folder_id is None:
            parent_folder_id = self.main_folder_id

        print(f"Обработка папки ID: {parent_folder_id}...")
        query = f"'{parent_folder_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        results = self.drive_service.files().list(q=query, fields="files(id, name)").execute()
        folders = results.get('files', [])

        if not folders:
            print(f"Нет вложенных папок в папке ID: {parent_folder_id}")

        for folder in folders:
            folder_id = folder['id']
            folder_name = folder['name']
            print(f"Начата обработка вложенной папки: '{folder_name}' (ID: {folder_id})")
            # Убираем доступ по ссылке для текущей папки
            self.remove_link_sharing(folder_id)
            # Рекурсивно обрабатываем вложенные папки
            self.traverse_and_remove_sharing(folder_id)

    def remove_sharing_from_main_folder(self) -> None:
        """
        Удаляет доступ по ссылке для главной папки и всех вложенных.

        Это основной метод класса, который запускает рекурсивное удаление доступа по ссылке
        для указанной главной папки и всех её вложенных папок.
        """
        print("=== Запуск удаления доступа по ссылке для главной папки и всех вложенных папок ===")
        print(f"Начата обработка главной папки ID: {self.main_folder_id}")
        # Убираем доступ по ссылке для главной папки
        self.remove_link_sharing(self.main_folder_id)
        # Рекурсивно обходим все вложенные папки
        self.traverse_and_remove_sharing(self.main_folder_id)
        print("=== Удаление доступа по ссылке завершено ===")
