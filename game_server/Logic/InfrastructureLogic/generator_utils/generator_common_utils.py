# В файле generator_common_utils.py (или другом вашем утилитарном файле)

from game_server.services.logging.logging_setup import logger #
from typing import List, TypeVar

# Используем ваш настроенный логгер
from game_server.services.logging.logging_setup import logger #

_T = TypeVar('_T') # Для сохранения информации о типе элементов списка

def split_list_into_chunks(
    data_list: List[_T],
    chunk_size: int
) -> List[List[_T]]:
    """
    Разделяет список на более мелкие списки (чанки) заданного максимального размера.

    Args:
        data_list: Исходный список элементов для разделения.
        chunk_size: Максимальный размер одного чанка.

    Returns:
        Список, содержащий чанки (которые также являются списками).
        Возвращает пустой список, если исходный список пуст.

    Raises:
        ValueError: Если chunk_size меньше или равен нулю.
    """
    if not isinstance(data_list, list):
        # Логгируем ошибку, так как это может быть проблемой во время выполнения
        logger.error(f"Ошибка разделения на чанки: data_list не является списком (получен тип: {type(data_list)}).")
        # Можно также возбудить TypeError, если это предпочтительнее для вашего стиля обработки ошибок
        raise TypeError("data_list должен быть списком.")

    if not isinstance(chunk_size, int) or chunk_size <= 0:
        logger.error(f"Ошибка разделения на чанки: chunk_size должен быть положительным целым числом (получено: {chunk_size}).")
        raise ValueError("chunk_size должен быть положительным целым числом.")

    if not data_list:
        return []

    logger.debug(f"Разделение списка из {len(data_list)} элементов на чанки размером {chunk_size}.")
    
    chunks = [data_list[i:i + chunk_size] for i in range(0, len(data_list), chunk_size)]
    
    logger.debug(f"Список разделен на {len(chunks)} чанков.")
    return chunks

# Пример использования (для тестирования этой функции отдельно):
if __name__ == '__main__':
    logger.basicConfig(level=logger.DEBUG) # Настройка базового логгирования для примера

    # Тестовые случаи
    list1 = list(range(25))
    size1 = 10
    print(f"Список: {list1}, Размер чанка: {size1} -> Чанки: {split_list_into_chunks(list1, size1)}")
    # Ожидаемый результат: [[0, 1, ..., 9], [10, 11, ..., 19], [20, 21, ..., 24]]

    list2 = list(range(5))
    size2 = 10
    print(f"Список: {list2}, Размер чанка: {size2} -> Чанки: {split_list_into_chunks(list2, size2)}")
    # Ожидаемый результат: [[0, 1, 2, 3, 4]]

    list3 = []
    size3 = 5
    print(f"Список: {list3}, Размер чанка: {size3} -> Чанки: {split_list_into_chunks(list3, size3)}")
    # Ожидаемый результат: []

    list4 = list(range(10))
    size4 = 3
    print(f"Список: {list4}, Размер чанка: {size4} -> Чанки: {split_list_into_chunks(list4, size4)}")
    # Ожидаемый результат: [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9]]

    try:
        split_list_into_chunks(list(range(5)), 0)
    except ValueError as e:
        print(f"Перехвачена ожидаемая ошибка: {e}")

    try:
        split_list_into_chunks("не список", 5) # type: ignore
    except TypeError as e:
        print(f"Перехвачена ожидаемая ошибка: {e}")