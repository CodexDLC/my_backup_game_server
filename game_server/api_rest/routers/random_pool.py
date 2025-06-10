# game_server/api/routers/random_pool.py

from fastapi import APIRouter

from game_server.Logic.DomainLogic.Services.random_pool_logic import RandomPoolManager



router = APIRouter()

@router.post("/random/init_pool", summary="Создать или пересоздать пул чисел")
async def init_random_pool():
    """Удаляет текущий пул и создаёт новый"""
    try:
        manager = RandomPoolManager()
        await manager.init_pool()
        return {"status": "✅ Пул чисел создан!"}
    except Exception as e:
        print(f"❌ Ошибка в init_pool: {e}")
        return {"status": "❌ Ошибка!", "message": str(e)}


@router.get("/random/check_chance", summary="Проверить вероятность события")
async def check_chance(chance: float):
    """Проверяет, сработает ли случайное событие при заданной вероятности"""
    manager = RandomPoolManager()
    result = await manager.check_chance(chance)
    return {"chance": chance, "result": result}

@router.get("/random/stats", summary="Получить статистику пула чисел")
async def pool_stats():
    """Возвращает текущее состояние пула чисел"""
    manager = RandomPoolManager()
    stats = await manager.get_stats()
    return stats


random_pool_router = router  # 🔥 Экземпляр маршрутов для использования в приложении