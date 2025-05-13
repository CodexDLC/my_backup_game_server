import os
from .logging_config import logger



def update_all_init_files(root_dir):
    """
    Обновляет __init__.py в каждой папке с импортами всех файлов.
    :param root_dir: Корневая папка, где будут проходить обновления.
    """
    try:
        # INFO Исключаем кешированные папки __pycache__
        for dirpath, dirnames, filenames in os.walk(root_dir):
            dirnames[:] = [d for d in dirnames if d != "__pycache__"]  # INFO Убираем __pycache__

            init_path = os.path.join(dirpath, '__init__.py')

            if "__init__.py" in filenames:
                continue  # INFO Если файл уже есть, пропускаем

            # 🛠 Создание/обновление __init__.py
            with open(init_path, "w") as init_file:
                for file in filenames:
                    if file.endswith(".py") and file != "__init__.py":
                        module_name = file[:-3]
                        init_file.write(f"from .{module_name} import *\n")

                logger.info(f"INFO Файл {init_path} обновлён.")
        
        logger.info(f"INFO Все файлы __init__.py в {root_dir} обновлены.")
    except Exception as e:
        logger.error(f"ERROR Ошибка при обновлении __init__.py: {e}")

# 🏗 Запуск обновления файлов
if __name__ == "__main__":
    root_dir = "game_server"
    update_all_init_files(root_dir)
