# game_server/Logic/CoreServices/utils/resilience_utils.py

import time
from typing import final

# Используем @final, чтобы показать, что этот класс не предназначен для наследования,
# а является конкретной реализацией простого паттерна.
@final
class CircuitBreaker:
    """
    Простая реализация паттерна "Автоматический выключатель" (Circuit Breaker).

    Предотвращает повторные вызовы сервиса, который начал сбоить,
    давая ему время на восстановление.

    Атрибуты:
        max_fails (int): Количество сбоев, после которого выключатель "размыкается".
        reset_timeout (int): Время в секундах, по истечении которого
                             выключатель переходит в состояние "полуоткрыт"
                             и позволяет сделать одну пробную попытку.
    """
    def __init__(self, max_fails: int = 3, reset_timeout: int = 30):
        self._fail_count = 0
        self._last_fail_time = 0.0
        self.max_fails = max_fails
        self.reset_timeout = reset_timeout

    def allow_request(self) -> bool:
        """
        Проверяет, можно ли выполнить следующий запрос.

        Returns:
            bool: True, если выключатель "замкнут" (запросы разрешены), иначе False.
        """
        # Проверяем, не пора ли сбросить счетчик после таймаута
        if self._is_timeout_expired():
            self.reset()
        
        # Если количество сбоев меньше максимального, запрос разрешен
        return self._fail_count < self.max_fails

    def record_failure(self) -> None:
        """
        Регистрирует сбой. Увеличивает счетчик и обновляет время последнего сбоя.
        """
        self._fail_count += 1
        self._last_fail_time = time.monotonic()

    def record_success(self) -> None:
        """
        Регистрирует успешный вызов. Сбрасывает выключатель в исходное состояние.
        """
        self.reset()

    def reset(self) -> None:
        """
        Сбрасывает выключатель в "замкнутое" состояние.
        """
        self._fail_count = 0
        self._last_fail_time = 0.0

    @property
    def is_open(self) -> bool:
        """
        Свойство, показывающее, "разомкнут" ли выключатель в данный момент.
        """
        return not self.allow_request()

    def _is_timeout_expired(self) -> bool:
        """ Проверяет, истекло ли время сброса. """
        if self._last_fail_time == 0.0:
            return False
        return time.monotonic() - self._last_fail_time > self.reset_timeout

