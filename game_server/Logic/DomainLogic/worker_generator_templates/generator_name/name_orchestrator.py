# game_server/Logic/InfrastructureLogic/generator/name_orchestrator.py

from typing import Tuple, Any, Optional
# Импортируем логгер
from game_server.Logic.DomainLogic.worker_generator_templates.generator_name.generator_name_utils.item_name_generator import ItemNameGenerator
from game_server.Logic.InfrastructureLogic.logging.logging_setup import app_logger as logger

from game_server.Logic.DomainLogic.worker_generator_templates.generator_name.generator_name_utils.character_name_generator import CharacterNameGenerator

from game_server.Logic.DomainLogic.worker_generator_templates.generator_name.generator_name_utils.monster_name_generator import MonsterNameGenerator


class NameOrchestrator:
    """
    Класс-оркестратор для генерации различных типов имен.
    Предоставляет "обертки" для вызова специализированных генераторов.
    """

    @classmethod
    def generate_character_name(cls, gender: str) -> Tuple[str, str]:
        """
        Генерирует полное имя для персонажа (имя и фамилию).
        Args:
            gender (str): Пол персонажа ('male', 'female', 'other').
        Returns:
            Tuple[str, str]: Кортеж из имени и фамилии.
        """
        logger.debug(f"Запрос на генерацию имени персонажа для пола: {gender}")
        try:
            # Вызов специализированного генератора для персонажей
            return CharacterNameGenerator.generate_full_name(gender)
        except Exception as e:
            logger.error(f"Ошибка при генерации имени персонажа для пола '{gender}': {e}", exc_info=True)
            raise

    @classmethod
    def generate_monster_name(cls, monster_type_hint: str = "") -> str:
        """
        Генерирует имя для монстра.
        Args:
            monster_type_hint (str): Подсказка о типе монстра.
        Returns:
            str: Сгенерированное имя монстра.
        """
        logger.debug(f"Запрос на генерацию имени монстра (подсказка: {monster_type_hint})")
        try:
            # Вызов специализированного генератора для монстров
            return MonsterNameGenerator.generate_name(monster_type_hint)
        except Exception as e:
            logger.error(f"Ошибка при генерации имени монстра: {e}", exc_info=True)
            raise

    @classmethod
    def generate_item_name(
        cls,
        rarity_prefix: Optional[str],
        base_item_display_name: str,
        material_adjective: str,
        suffix_fragment: Optional[str] = None
    ) -> str:
        """
        Генерирует имя для предмета, делегируя вызов ItemNameGenerator.
        
        Args:
            rarity_prefix (Optional[str]): Префикс редкости.
            base_item_display_name (str): Отображаемое имя базового предмета.
            material_adjective (str): Прилагательное материала.
            suffix_fragment (Optional[str]): Фрагмент суффикса, может быть None.
        Returns:
            str: Сгенерированное имя предмета.
        """
        logger.debug(f"Запрос на генерацию имени предмета с компонентами: {rarity_prefix}, {base_item_display_name}, {material_adjective}, {suffix_fragment}")
        try:
            # Вызов специализированного генератора для предметов
            return ItemNameGenerator.generate_name(
                rarity_prefix=rarity_prefix,
                base_item_display_name=base_item_display_name,
                material_adjective=material_adjective,
                suffix_fragment=suffix_fragment
            )
        except Exception as e:
            logger.error(f"Ошибка при генерации имени предмета: {e}", exc_info=True)
            raise

    # Здесь можно добавлять другие методы-обертки для новых типов генерации имен.