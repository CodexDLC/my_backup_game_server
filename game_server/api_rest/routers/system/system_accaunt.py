from fastapi import FastAPI, APIRouter

from game_server.Logic.ApplicationLogic.api_reg.regestration_accaount import CreateAccountManager


router = APIRouter()  # Используем APIRouter, а не FastAPI!

@router.post("/create_account")
async def create_account(identifier_type: str, identifier_value: str, username: str, avatar: str = None, locale: str = None, region: str = None):
    async with CreateAccountManager() as manager:
        return await manager.create_account(identifier_type, identifier_value, username, avatar, locale, region)

@router.put("/update_account")
async def update_account(identifier_type: str, identifier_value: str, update_data: dict):
    async with CreateAccountManager() as manager:
        return await manager.update_account(identifier_type, identifier_value, update_data)

@router.delete("/delete_account")
async def delete_account(identifier_type: str, identifier_value: str):
    async with CreateAccountManager() as manager:
        return await manager.delete_account(identifier_type, identifier_value)

@router.get("/generate_registration_link")
async def generate_registration_link(identifier_type: str, identifier_value: str):
    async with CreateAccountManager() as manager:
        return await manager.generate_registration_link(identifier_type, identifier_value)

system_accaunt_router = router
