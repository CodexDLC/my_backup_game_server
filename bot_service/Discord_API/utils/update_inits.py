import os
import game_server.logger.logger_config as logger
import argparse

# Настройка логирования


def update_all_init_files(root_dir):
    try:
        for dirpath, dirnames, filenames in os.walk(root_dir):
            EXCLUDED_FOLDERS = ["cogs"]  # Исключаем папку cogs
            
            # Проверяем, нужно ли пропустить папку
            if any(excluded in dirpath for excluded in EXCLUDED_FOLDERS):
                continue  # Пропускаем обновление

            init_path = os.path.join(dirpath, '__init__.py')  # Путь к __init__.py

            # Создание/обновление файла __init__.py
            with open(init_path, 'w') as init_file:
                for file in filenames:
                    if file.endswith('.py') and file != '__init__.py':
                        module_name = file[:-3]  # Убираем расширение .py
                        init_file.write(f"from .{module_name} import *\n")

                logger.info(f"Файл {init_path} успешно обновлён.")
        logger.info(f"Все файлы __init__.py в {root_dir} обновлены.")
    except Exception as e:
        logger.error(f"Ошибка при обновлении файлов __init__.py: {e}")

def update_server_directory():
    """
    Обновляет __init__.py в директории главного сервера.
    """
    directory = "/opt/new_order_rpg/database/server_db"
    logger.info(f"Запуск обновления импортов в папке {directory}...")
    update_all_init_files(directory)
    logger.info("Процесс завершён для сервера.")

def update_discord_directory():
    """
    Обновляет __init__.py в директории Discord API.
    """
    directory = "/opt/new_order_rpg/Discord_API"
    logger.info(f"Запуск обновления импортов в папке {directory}...")
    update_all_init_files(directory)
    logger.info("Процесс завершён для Discord API.")

if __name__ == "__main__":
    # Аргументы командной строки для выбора директории
    parser = argparse.ArgumentParser(description="Обновление __init__.py файлов в различных папках")
    parser.add_argument(
        "target", 
        type=str, 
        choices=["server", "discord"], 
        help="Выберите, какую директорию обновить: 'server' или 'discord'"
    )
    args = parser.parse_args()

    if args.target == "server":
        update_server_directory()
    elif args.target == "discord":
        update_discord_directory()