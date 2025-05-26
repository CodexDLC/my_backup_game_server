import os
import logging
from concurrent.futures import ThreadPoolExecutor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

base_path = os.path.dirname(os.path.abspath(__file__))
exclude_dirs = {"venv", ".env", "__pycache__", ".git", ".gitignore"}
exclude_files = {"setup.py", "config.py"}  # Файлы, которые не нужно импортировать

def safe_read_file(path):
    """Безопасное чтение файла с обработкой разных кодировок"""
    encodings = ['utf-8', 'cp1251', 'latin-1']  # Попробуем самые распространенные кодировки
    for encoding in encodings:
        try:
            with open(path, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    return None

def create_init_files(folder):
    try:
        for root, dirs, files in os.walk(folder):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            init_path = os.path.join(root, "__init__.py")
            py_files = [
                f.replace(".py", "") 
                for f in files 
                if (f.endswith(".py") and 
                    f != "__init__.py" and 
                    f not in exclude_files)
            ]
            
            if not py_files:
                if os.path.exists(init_path):
                    continue
                # Создаем пустой __init__.py даже если нет других файлов
                with open(init_path, 'w', encoding='utf-8') as f:
                    f.write("")
                continue
                
            content = f"__all__ = {py_files}\n\n" + "".join(
                f"from .{file} import *\n" for file in py_files
            )
            
            if os.path.exists(init_path):
                existing_content = safe_read_file(init_path)
                if existing_content is None:
                    logger.warning(f"⚠️ Не удалось прочитать файл {init_path} (проблема с кодировкой)")
                    continue
                if content == existing_content:
                    continue
                        
            with open(init_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
    except Exception as e:
        logger.error(f"Error processing {folder}: {str(e)}", exc_info=True)

if __name__ == "__main__":
    folders_to_scan = [
        os.path.join(base_path, "game_server"),
        os.path.join(base_path, "bot_service"), 
        os.path.join(base_path, "website")
    ]
    
    with ThreadPoolExecutor() as executor:
        list(executor.map(create_init_files, folders_to_scan))  # list() для немедленного выполнения
    
    logger.info("✅ __init__.py files updated")