# transport/http_client/routes/gateway_api_impl.py
import aiohttp
from typing import Optional, Dict, Any
from game_server.common_contracts.api_models.gateway_api import BotAcknowledgementRequest
from game_server.config.logging.logging_setup import app_logger as logger


from game_server.app_discord_bot.transport.http_client.interfaces.i_gateway_api import IGatewayAPIRoutes


class GatewayAPIRoutesImpl(IGatewayAPIRoutes):
    def __init__(self, session: aiohttp.ClientSession, base_url: str):
        self._session = session
        self._base_url = f"{base_url}/gateway/commands"

    async def acknowledge_command(self, command_id: str, data: BotAcknowledgementRequest) -> Optional[Dict[str, Any]]:
        url = f"{self._base_url}/{command_id}/ack"
        async with self._session.post(url, json=data.model_dump()) as response:
            if response.status == 200: return await response.json()
            logger.error(f"ACK failed: {response.status}, {await response.text()}")
            return None
