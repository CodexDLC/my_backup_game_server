# game_server/Logic/DomainLogic/CharacterLogic/character_creation_helpers.py
import logging
from typing import List, Dict, Any

from game_server.Logic.InfrastructureLogic.DataAccessLogic.manager.generators.ORM_character_pool_manager import CharacterPoolRepository
from game_server.database.models.models import CharacterPool, Skills

logger = logging.getLogger(__name__)

async def select_template_from_pool(pool_repo: CharacterPoolRepository) -> CharacterPool | None:
    """Хелпер для инкапсуляции логики выбора персонажа из пула."""
    logger.debug("Выбор шаблона персонажа из пула...")
    return await pool_repo.find_one_available_and_lock()

def precalculate_skill_xp_data(character_id: int, stats: Dict[str, Any], all_skills: List[Skills]) -> List[Dict[str, Any]]:
    """
    Предрасчитывает базовый опыт за тик для каждого навыка на основе SPECIAL-статов.
    Формула: (main_special * 2) + (secondary_special * 1)
    """
    logger.debug(f"Предрасчет опыта за тик для персонажа {character_id}...")
    xp_data_list = []
    
    character_stats = {
        "strength": stats.get('strength', 0), "perception": stats.get('perception', 0),
        "endurance": stats.get('endurance', 0), "charisma": stats.get('charisma', 0),
        "intelligence": stats.get('intelligence', 0), "agility": stats.get('agility', 0),
        "luck": stats.get('luck', 0),
    }

    for skill in all_skills:
        main_stat_name = skill.main_special
        secondary_stat_name = skill.secondary_special

        if not main_stat_name or not secondary_stat_name:
            logger.warning(f"Навык '{skill.skill_key}' пропущен: не определены main_special или secondary_special.")
            continue

        main_stat_value = character_stats.get(main_stat_name, 0)
        secondary_stat_value = character_stats.get(secondary_stat_name, 0)
        xp_generated = (main_stat_value * 2) + (secondary_stat_value * 1)

        xp_data_list.append({
            "character_id": character_id, "skill_id": skill.skill_id, "xp_generated": xp_generated,
        })
    return xp_data_list