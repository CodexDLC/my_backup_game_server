from fastapi import APIRouter

from game_server.Logic.InfrastructureLogic.DataAccessLogic.manager.system.world.ORM_state_entities import StateEntitiesManager



router = APIRouter()

# 🏆 API для `state_entities`
@router.get("/state-entities", summary="Получить список всех состояний")
async def get_all_states():
    result = await StateEntitiesManager.get_all_states()
    return result

@router.get("/state-entities/{access_code}", summary="Получить данные состояния по `access_code`")
async def get_state_by_access_code(access_code: int):
    result = await StateEntitiesManager.get_state_by_access_code(access_code)
    return result





system_mapping_route = router