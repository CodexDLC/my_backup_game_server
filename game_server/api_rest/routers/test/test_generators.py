# game_server/api/endpoints/test_generators.py

from fastapi import APIRouter, Query, HTTPException
from typing import Optional, Tuple, Union, Dict, Any

# Импортируем наш оркестратор имён

# Импортируем логгер
from game_server.Logic.DomainLogic.worker_autosession.generator_name.name_orchestrator import NameOrchestrator
from game_server.services.logging.logging_setup import logger

router = APIRouter()

@router.get("/generate_name/", response_model=Dict[str, Any], summary="Сгенерировать имя по типу")
async def generate_name_endpoint(
    name_type: str = Query(..., description="Тип генерируемого имени (например, 'character', 'monster', 'item')"),
    gender: Optional[str] = Query(None, description="Пол для персонажа (например, 'male', 'female', 'other'). Обязателен для 'character'."),
    type_hint: Optional[str] = Query(None, description="Дополнительная подсказка для типа монстра/предмета.")
) -> Dict[str, Any]:
    """
    Эндпоинт для генерации различных типов имен.

    - **name_type**: Укажите тип имени, который нужно сгенерировать.
        - 'character': Генерирует имя персонажа (требует параметра 'gender').
        - 'monster': Генерирует имя монстра (может использовать 'type_hint').
        - 'item': Генерирует имя предмета (может использовать 'type_hint').
    - **gender**: Пол персонажа. Обязателен, если `name_type` = 'character'.
    - **type_hint**: Необязательная подсказка для генераторов монстров/предметов.
    """
    logger.info(f"Получен запрос на генерацию имени: type={name_type}, gender={gender}, hint={type_hint}")

    generated_name: Union[str, Tuple[str, str]] = ""

    try:
        if name_type.lower() == "character":
            if not gender:
                logger.warning("Для типа 'character' параметр 'gender' обязателен.")
                raise HTTPException(status_code=400, detail="Для генерации имени персонажа требуется указать пол (gender).")
            first_name, last_name = NameOrchestrator.generate_character_name(gender)
            generated_name = {"first_name": first_name, "last_name": last_name, "full_name": f"{first_name} {last_name}"}
        elif name_type.lower() == "monster":
            generated_name = {"name": NameOrchestrator.generate_monster_name(type_hint if type_hint else "")}
        elif name_type.lower() == "item":
            generated_name = {"name": NameOrchestrator.generate_item_name(type_hint if type_hint else "")}
        else:
            logger.warning(f"Неизвестный тип генерации имени: {name_type}")
            raise HTTPException(status_code=400, detail=f"Неизвестный тип генерации имени: {name_type}")

        logger.info(f"Сгенерировано имя: {generated_name}")
        return {"status": "success", "data": generated_name}

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception(f"Произошла ошибка при генерации имени: {e}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера при генерации имени: {e}")
    


test_generators_router = router