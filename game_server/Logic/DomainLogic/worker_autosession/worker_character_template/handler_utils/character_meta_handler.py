# Logic/DomainLogic/handlers_template/worker_character_template/handler_utils/character_meta_handler.py

from typing import Dict, Any

# --- Логгер ---
# Предполагается, что вы импортируете и используете ваш настроенный логгер
# from game_server.services.logging.logging_setup import logger
# Временная заглушка:
# logging.basicConfig(level=logging.DEBUG) # Для локального тестирования этого файла

# --- Константы ---
# TARGET_POOL_QUALITY_DISTRIBUTION будет передаваться как параметр,
# так как он может быть частью более общей конфигурации, доступной
# функции-оркестратору character_batch_processor.py.
# Имя самого высокого уровня качества также будет передаваться.

async def get_character_meta_attributes(
    quality_level: str,
    highest_quality_level_name: str,
    target_quality_distribution: Dict[str, float]
) -> Dict[str, Any]:
    """
    Определяет мета-атрибуты персонажа, такие как is_unique и rarity_score.

    Args:
        quality_level (str): Уровень качества персонажа.
        highest_quality_level_name (str): Имя самого высокого уровня качества,
                                          используемого для определения is_unique.
        target_quality_distribution (Dict[str, float]): Словарь, где ключи - уровни качества,
                                                       а значения - их целевая доля в пуле (0.0 до 1.0).

    Returns:
        Dict[str, Any]: Словарь с ключами "is_unique" (bool) и "rarity_score" (int).
    """


    # Определение is_unique
    is_unique = (quality_level == highest_quality_level_name)


    # Расчет rarity_score
    # Примерная логика: чем меньше процент качества в пуле, тем выше rarity_score.
    # Можно использовать обратную величину процента, умноженную на некий коэффициент.
    # Или более сложную шкалу.
    # target_quality_distribution содержит доли, например, {"SUPERIOR_ELITE_QUALITY": 0.001}
    
    percentage = target_quality_distribution.get(quality_level)

    if percentage is None:
 
        rarity_score = 100 # Значение по умолчанию, если качество не найдено в распределении
    elif percentage <= 0: # Избегаем деления на ноль или отрицательных значений
 
        rarity_score = 100000 # Очень высокий скор для крайне редких или ошибочных случаев
    else:
        # Примерная формула: чем меньше процент, тем больше очков.
        # (1 / процент) дает хороший разброс. Множитель для масштабирования.
        # Например, если 0.001 (0.1%) -> (1/0.001) * 1 = 1000
        # Если 0.05 (5%) -> (1/0.05) * 1 = 20
        # Если 0.5 (50%) -> (1/0.5) * 1 = 2
        # Чтобы получить более "красивые" числа, можно добавить множитель, например 100:
        # 0.1% -> 100000
        # 5%   -> 2000
        # 50%  -> 200
        # Подберите коэффициент или формулу, которая вам подходит.
        base_score = (1 / percentage)
        rarity_score = int(base_score * 100) # Примерный множитель
        # Можно также ввести минимальное и максимальное значение для rarity_score.
        # rarity_score = max(10, min(rarity_score, 100000)) 



    return {
        "is_unique": is_unique,
        "rarity_score": rarity_score
    }