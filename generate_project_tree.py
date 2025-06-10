import os

def generate_full_tree(startpath, exclude_dirs=None, exclude_files=None, exclude_extensions=None):
    """
    Генерирует и печатает полную структуру директорий и файлов для указанного пути,
    исключая указанные папки, файлы и расширения.
    """
    if exclude_dirs is None:
        exclude_dirs = [
            '.git', '.venv', 'env', 'venv', # Виртуальные окружения
            '__pycache__', '.pytest_cache', '.idea', # Кэш и IDE
            'build', 'dist', 'propcache', # Сборочные и кэш-папки
            '.vscode', # Конфигурации VS Code
        ]
    if exclude_files is None:
        exclude_files = ['.DS_Store', 'Thumbs.db', 'desktop.ini']
    if exclude_extensions is None:
        exclude_extensions = ['.pyc', '.bak', '.tmp', '.log', '.orig', '.rej'] # Типичные временные/кэш файлы

    # Создадим наборы для быстрых проверок
    exclude_dirs_set = set(exclude_dirs)
    exclude_files_set = set(exclude_files)
    exclude_extensions_set = set(exclude_extensions)

    # Проверка существования пути
    if not os.path.exists(startpath):
        print(f"Ошибка: Папка '{startpath}' не существует.")
        return
    if not os.path.isdir(startpath):
        print(f"Ошибка: '{startpath}' не является папкой.")
        return

    # Печатаем корневую папку один раз, если она не является исключенной
    base_start_name = os.path.basename(startpath)
    if base_start_name in exclude_dirs_set or base_start_name.endswith(('.dist-info', '.egg-info')):
        print(f"Ошибка: Стартовая папка '{startpath}' сама является исключенной или служебной.")
        return

    print(f"{base_start_name}/")

    # Используем os.walk
    for root, dirs, files in os.walk(startpath):
        # Определение текущего уровня вложенности относительно startpath
        relative_path = os.path.relpath(root, startpath)
        if relative_path == ".": # Если это корневая папка, то относительный путь "."
            level = 0
        else:
            level = relative_path.count(os.sep) + 1 # +1 потому что os.path.relpath для 'a/b' относительно 'a' будет 'b', count=0

        # Отступ для текущей папки и ее содержимого
        indent = ' ' * 4 * level
        
        base_name = os.path.basename(root)

        # Проверяем, не является ли текущая папка (root) одной из исключенных
        # Если это так, мы её не печатаем и не спускаемся в неё
        if base_name in exclude_dirs_set or base_name.endswith(('.dist-info', '.egg-info')):
            dirs[:] = [] # Не заходим в эту папку и ее подпапки
            continue # Пропускаем остальную часть цикла для этой папки
            
        # Печатаем текущую директорию, если это не корневая (которая уже напечатана)
        if root != startpath:
            print(f"{indent}├── {base_name}/")

        # Отступ для элементов внутри текущей папки (на один уровень глубже)
        item_indent = ' ' * 4 * (level + 1)

        # Фильтруем и печатаем файлы
        for f in sorted(files): # Сортируем файлы для более чистого вывода
            file_name, file_ext = os.path.splitext(f)
            if f in exclude_files_set or file_ext in exclude_extensions_set:
                continue
            print(f"{item_indent}├── {f}")

        # Фильтруем список dirs для следующей итерации os.walk (для надежности)
        dirs[:] = [d for d in dirs if d not in exclude_dirs_set and not d.endswith(('.dist-info', '.egg-info'))]


# Функции create_folder_interactively остаются без изменений
def create_folder_interactively():
    """
    Запрашивает у пользователя имя папки для создания и создает ее.
    """
    folder_name = input("\nВведите имя папки, которую хотите создать (или оставьте пустым для отмены): ").strip()
    if not folder_name:
        print("Создание папки отменено.")
        return

    try:
        os.makedirs(folder_name, exist_ok=True)
        print(f"Папка '{folder_name}' успешно создана (если она не существовала).")
    except Exception as e:
        print(f"Ошибка при создании папки '{folder_name}': {e}")


# --- Запуск скрипта ---
if __name__ == "__main__":
    project_root = os.getcwd() # Скрипт будет запускаться из корня проекта

    while True:
        print("\n--- Меню скрипта ---")
        print("1. Показать структуру (папки + файлы) для указанного пути (с исключениями)")
        print("2. Показать ПОЛНУЮ структуру (папки + файлы) всего проекта (с исключениями)") # Изменено название
        print("3. Создать новую папку")
        print("4. Выход")
        
        choice = input("Выберите действие (1, 2, 3 или 4): ").strip()

        if choice == '1':
            relative_path = input("Введите путь к папке (относительно текущей директории, например, 'game_server/Logic'): ").strip()
            if relative_path:
                full_path = os.path.join(project_root, relative_path)
                print(f"\nСтруктура указанной папки:")
                generate_full_tree(full_path)
            else:
                print("Путь не указан. Возврат в меню.")
        elif choice == '2':
            print(f"\nПолная структура проекта:")
            generate_full_tree(project_root)
            print("\n--- Конец структуры ---")
        elif choice == '3':
            create_folder_interactively()
        elif choice == '4':
            print("Выход из скрипта.")
            break
        else:
            print("Неверный выбор. Пожалуйста, введите 1, 2, 3 или 4.")