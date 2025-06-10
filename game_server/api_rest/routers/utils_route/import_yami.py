from fastapi import APIRouter, HTTPException

from game_server.database.script_import.export_yaml import export_to_yaml




router = APIRouter()

@router.post("/export", summary="Вызвать скрипт экспорта данных")
async def export_data(schema: str):
    """Вызывает существующий скрипт экспорта по указанной `schema`"""
    try:
        await export_to_yaml(schema)
        return {"status": "✅ Экспорт завершён!", "folder": f"import_{schema}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"❌ Ошибка экспорта: {str(e)}")



import_yami_route = router
    