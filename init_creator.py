import os
import logging
import ast
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Обновленный список исключений
exclude_dirs = {"venv", ".env", "__pycache__", ".git", ".gitignore", "game_server/api/routers"}
exclude_files = {"setup.py", "config.py"}

def safe_read_file(path: str) -> Optional[str]:
    """Безопасное чтение файла с обработкой разных кодировок"""
    encodings = ['utf-8', 'cp1251', 'latin-1']
    for encoding in encodings:
        try:
            with open(path, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    return None

def generate_init_content(root: str, files: List[str]) -> str:
    """Генерирует содержимое для __init__.py файла"""
    imports = []
    all_items = []
    is_routers_folder = "routers" in root.replace("\\", "/").split("/")
    
    for file in files:
        if not file.endswith(".py") or file == "__init__.py" or file in exclude_files:
            continue
        
        module_name = file.replace(".py", "")
        
        # Особые случаи
        if module_name == "random_pool_route":
            imports.append("from ..random_pool_route import random_pool_route\n")
            all_items.append("random_pool_route")
            continue
            
        # Обработка routers
        if is_routers_folder:
            import_line = f"from .{module_name} import {module_name}_router\n"
            imports.append(import_line)
            all_items.append(f"{module_name}_router")
        else:
            # Стандартная обработка
            imports.append(f"from . import {module_name}\n")
            all_items.append(module_name)
    
    if not all_items:
        return ""
    
    content = f"__all__ = {sorted(all_items)}\n\n" + "".join(sorted(imports))
    return content

def create_init_files(folder: str):
    """Создает или обновляет __init__.py файлы в переданной папке"""
    try:
        for root, dirs, files in os.walk(folder):
            # Фильтруем директории, исключая `game_server/api/routers`
            dirs[:] = [d for d in dirs if os.path.join(root, d) not in exclude_dirs]
            
            init_path = os.path.join(root, "__init__.py")
            py_files = [f for f in files if f.endswith(".py") and f != "__init__.py" and f not in exclude_files]
            
            if not py_files:
                if os.path.exists(init_path):
                    continue
                with open(init_path, 'w', encoding='utf-8') as f:
                    f.write("")
                continue
                
            content = generate_init_content(root, py_files)
            
            if os.path.exists(init_path):
                existing_content = safe_read_file(init_path)
                if existing_content is None:
                    logger.warning(f"⚠️ Не удалось прочитать файл {init_path} (проблема с кодировкой)")
                    continue
                if content == existing_content:
                    continue
                    
            with open(init_path, 'w', encoding='utf-8') as f:
                f.write(content if content else "# Empty __init__.py file\n")
                
    except Exception as e:
        logger.error(f"Error processing {folder}: {str(e)}", exc_info=True)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Обновление __init__.py файлов в указанной папке")
    parser.add_argument("folder", type=str, help="Путь до папки для обработки")
    args = parser.parse_args()
    
    create_init_files(args.folder)
    
    logger.info(f"✅ __init__.py файлы обновлены в {args.folder}, кроме game_server/api/routers")
