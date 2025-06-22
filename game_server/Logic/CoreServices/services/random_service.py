import random
import secrets
import os
import numpy as np
from typing import List, Any, Optional

class RandomService:
    def __init__(self, crypto_mode: bool = False):
        """
        :param crypto_mode: Если True, использует криптографически стойкие генераторы
        """
        self.crypto_mode = crypto_mode
        self._init_generators()
        
    def _init_generators(self):
        """Инициализация генераторов при создании сервиса"""
        seed = os.urandom(32)  # 256 бит энтропии
        
        # Основной генератор для игровой логики
        self.main_rng = random.Random(seed)
        
        # Генератор для безопасности
        self.crypto_rng = secrets.SystemRandom(seed)
        
        # Быстрый генератор для массовых операций
        self.fast_rng = np.random.Generator(np.random.PCG64(seed))
    
    def reseed(self, new_seed: Optional[bytes] = None):
        """Переинициализация генераторов"""
        seed = new_seed or os.urandom(32)
        self.main_rng.seed(seed)
        self.fast_rng = np.random.Generator(np.random.PCG64(seed))
    
    # --- Основные методы ---
    def randint(self, a: int, b: int, entity_id: Optional[str] = None) -> int:
        """Случайное целое в диапазоне [a, b]"""
        rng = self._select_rng(entity_id)
        if self.crypto_mode:
            return self.crypto_rng.randint(a, b)
        return rng.randint(a, b)
    
    def uniform(self, a: float, b: float) -> float:
        """Равномерное распределение"""
        return self.main_rng.uniform(a, b)
    
    def gauss(self, mu: float, sigma: float) -> float:
        """Нормальное распределение"""
        return self.main_rng.gauss(mu, sigma)
    
    def choice(self, seq: List[Any], entity_id: Optional[str] = None) -> Any:
        """Случайный элемент из последовательности"""
        rng = self._select_rng(entity_id)
        return rng.choice(seq)
    
    def weighted_choice(self, items: List[Any], weights: List[float]) -> Any:
        """Выбор с учетом весов"""
        return self.main_rng.choices(items, weights=weights, k=1)[0]
    
    def shuffle(self, seq: List[Any], entity_id: Optional[str] = None) -> None:
        """Перемешивание последовательности"""
        rng = self._select_rng(entity_id)
        rng.shuffle(seq)
    
    # --- Оптимизированные методы для массовых операций ---
    def fast_rand_array(self, shape: tuple, dtype=np.float32):
        """Быстрая генерация массива случайных чисел"""
        return self.fast_rng.random(shape, dtype=dtype)
    
    def fast_randint(self, low: int, high: int, size: int) -> np.ndarray:
        """Быстрая генерация целых чисел"""
        return self.fast_rng.integers(low, high, size)
    
    # --- Специализированные игровые методы ---
    def critical_hit(self, base_chance: float, luck_factor: float = 1.0) -> bool:
        """Определение критического удара"""
        return self.main_rng.random() < (base_chance * luck_factor)
    
    def loot_drop(self, drop_table: dict) -> Optional[dict]:
        """Определение выпавшего лута"""
        rand_val = self.main_rng.random()
        cumulative = 0.0
        for item, prob in drop_table.items():
            cumulative += prob
            if rand_val <= cumulative:
                return item
        return None
    
    # --- Внутренние методы ---
    def _select_rng(self, entity_id: Optional[str] = None) -> random.Random:
        """Выбор генератора на основе контекста"""
        if entity_id:
            # Создаем детерминированный генератор для сущности
            return random.Random(f"{entity_id}-{self.main_rng.random()}".encode())
        return self.main_rng