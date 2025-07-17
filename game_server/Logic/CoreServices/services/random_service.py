# game_server/Logic/CoreServices/services/random_service.py

import random
import secrets
import os
import numpy as np
import logging # ДОБАВЛЕНО: Импортируем logging для типизации logger
from typing import List, Any, Optional

class RandomService:
    def __init__(self, crypto_mode: bool = False, logger: logging.Logger = None): # ИЗМЕНЕНИЕ: Добавлен logger с дефолтным значением None
        """
        :param crypto_mode: Если True, использует криптографически стойкие генераторы.
        :param logger: Экземпляр логгера для логирования.
        """
        self.crypto_mode = crypto_mode
        # ИЗМЕНЕНИЕ: Сохраняем переданный логгер. Если не передан, создаем свой.
        self.logger = logger if logger is not None else logging.getLogger(self.__class__.__name__)
        self._init_generators()
        self.logger.info("✅ RandomService инициализирован.")
        
    def _init_generators(self):
        """Инициализирует генераторы при создании сервиса."""
        # Генерация 256 бит энтропии в виде байтовой строки
        byte_seed = os.urandom(32) 
        
        # Преобразование байтовой строки в целое число для NumPy's PCG64
        # Используется 'big' endian для интерпретации байтов как большого целого числа
        # Первый аргумент должен быть bytes или bytearray
        numeric_seed = int.from_bytes(byte_seed, 'big')
        
        # Основной генератор для игровой логики (принимает байтовые строки)
        self.main_rng = random.Random(byte_seed) 
        
        # Криптографически стойкий генератор (не принимает сид)
        self.crypto_rng = secrets.SystemRandom()
        
        # Быстрый генератор для массовых операций (требует целочисленный сид)
        # Передаем преобразованный numeric_seed в PCG64
        self.fast_rng = np.random.Generator(np.random.PCG64(numeric_seed))
    
    def reseed(self, new_seed: Optional[bytes] = None):
        """Повторно инициализирует генераторы."""
        # Если new_seed не предоставлен, генерируем новый
        byte_seed = new_seed or os.urandom(32)
        
        # Преобразование байтовой строки в целое число для NumPy's PCG64
        numeric_seed = int.from_bytes(byte_seed, 'big')

        self.main_rng.seed(byte_seed)
        # Передаем преобразованный numeric_seed в PCG64
        self.fast_rng = np.random.Generator(np.random.PCG64(numeric_seed))
    
    # --- Основные методы ---
    def randint(self, a: int, b: int) -> int:
        """Случайное целое число в диапазоне [a, b]."""
        if self.crypto_mode:
            return self.crypto_rng.randint(a, b)
        return self.main_rng.randint(a, b)
    
    # ИЗМЕНЕНИЕ: Устранена дублирующаяся сигнатура метода choice
    def choice(self, seq: List[Any]) -> Any:
        """Случайный элемент из последовательности."""
        if self.crypto_mode:
            return self.crypto_rng.choice(seq)
        return self.main_rng.choice(seq)
    
    def uniform(self, a: float, b: float) -> float:
        """Равномерное распределение."""
        return self.main_rng.uniform(a, b)
    
    def gauss(self, mu: float, sigma: float) -> float:
        """Нормальное распределение."""
        return self.main_rng.gauss(mu, sigma)
    
    # ИЗМЕНЕНИЕ: Переименовал дублирующий choice, чтобы он не конфликтовал с основным
    def choice_with_entity_context(self, seq: List[Any], entity_id: Optional[str] = None) -> Any:
        """Случайный элемент из последовательности, потенциально детерминированный для сущности."""
        rng = self._select_rng(entity_id)
        return rng.choice(seq)
    
    def weighted_choice(self, items: List[Any], weights: List[float]) -> Any:
        """Взвешенный случайный выбор."""
        return self.main_rng.choices(items, weights=weights, k=1)[0]
    
    def shuffle(self, seq: List[Any], entity_id: Optional[str] = None) -> None:
        """Перемешивает последовательность."""
        rng = self._select_rng(entity_id)
        rng.shuffle(seq)
    
    # --- Оптимизированные методы для массовых операций ---
    def fast_rand_array(self, shape: tuple, dtype=np.float32):
        """Быстрая генерация массива случайных чисел."""
        return self.fast_rng.random(shape, dtype=dtype)
    
    def fast_randint(self, low: int, high: int, size: int) -> np.ndarray:
        """Быстрая генерация целых чисел."""
        return self.fast_rng.integers(low, high, size)
    
    # --- Специализированные игровые методы ---
    def critical_hit(self, base_chance: float, luck_factor: float = 1.0) -> bool:
        """Определяет критический удар."""
        return self.main_rng.random() < (base_chance * luck_factor)
    
    def loot_drop(self, drop_table: dict) -> Optional[dict]:
        """Определяет выпадение лута."""
        rand_val = self.main_rng.random()
        cumulative = 0.0
        for item, prob in drop_table.items():
            cumulative += prob
            if rand_val <= cumulative:
                return item
        return None
    
    # --- Внутренние методы ---
    def _select_rng(self, entity_id: Optional[str] = None) -> random.Random:
        """Выбирает генератор на основе контекста."""
        if entity_id:
            return random.Random(f"{entity_id}-{self.main_rng.random()}".encode())
        return self.main_rng