# game_server/Logic/InfrastructureLogic/DataAccessLogic/app_post/repository_groups/meta_data_1lvl/meta_data_1lvl_config.py

# Импорты реализаций репозиториев
from .character_pool_repository_impl import CharacterPoolRepositoryImpl
# ДОБАВЛЕНО: Импорт EquipmentTemplateRepositoryImpl
from .equipment_template_repository_impl import EquipmentTemplateRepositoryImpl


# Импорты интерфейсов
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.meta_data_1lvl.interfaces_meta_data_1lvl import (
    ICharacterPoolRepository,
    IEquipmentTemplateRepository # <--- Убедитесь, что этот интерфейс существует
    # ДОБАВЛЕНО: Если есть интерфейс для StaticItemTemplate, его тоже можно добавить
    # IStaticItemTemplateRepository
)


# Конфигурация для группы репозиториев 'meta_data_1lvl'
meta_data_1lvl_repo_config = [
    {
        "name": "character_pool_repository",
        "implementation": CharacterPoolRepositoryImpl,
        "interface": ICharacterPoolRepository
    },
    # ДОБАВЛЕНО: Конфигурация для EquipmentTemplateRepository
    {
        "name": "equipment_template_repository", # Имя, по которому будет доступен в RepositoryManager
        "implementation": EquipmentTemplateRepositoryImpl,
        "interface": IEquipmentTemplateRepository
    },
    # Если в будущем будут другие репозитории в этой группе, добавьте их сюда.
    # Например, если вы хотите включить StaticItemTemplateRepositoryImpl в эту конфигурацию:
    # {
    #     "name": "static_item_template_repository",
    #     "implementation": StaticItemTemplateRepositoryImpl, # Убедитесь, что импортирован
    #     "interface": IStaticItemTemplateRepository # Убедитесь, что импортирован
    # },
]